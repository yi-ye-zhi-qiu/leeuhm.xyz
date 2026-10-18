#!/usr/bin/env bash
# First-time deployment of Terraform's remote state (Azure), the application
# secrets' Key Vault (Azure) and the site assets bucket (Cloudflare R2), for one
# environment:
#
#   ./first-time-deployment.sh dev
#   ./first-time-deployment.sh prod
#
# It's safe to re-run: Terraform only applies what's missing or changed, and
# asks for confirmation before each apply.
#
# Before running it, once, by hand:
#
# Azure
#   1. Create an Azure account with a subscription (Portal > Subscriptions >
#      Add, e.g. Pay-As-You-Go). You need to be its Owner (true when you create
#      it), to give yourself access to the Key Vault's secrets.
#   2. Install the Azure CLI, https://learn.microsoft.com/cli/azure/install-azure-cli
#      The script signs in with it and uses its selected subscription. With
#      several subscriptions, select yours first:
#
#        az login
#        az account list --output table
#        az account set --subscription "<subscription name>"
#
# Cloudflare
#   3. Note your account ID (Dashboard > Account home, or any zone's overview).
#   4. Enable R2 (Dashboard > R2 Object Storage), which needs a payment method
#      even for the free tier.
#   5. For prod: add `espresso.gg` as a zone, switch its nameservers to
#      Cloudflare's, and note its zone ID (the zone's overview page).
#   6. Create an account API token for Terraform (Manage Account > Account API
#      Tokens > Create Token > Custom Token) with:
#        - Account > Workers R2 Storage > Edit
#        - Account > Account API Tokens > Edit (to create the crawler's write
#          token)
#        - Zone > DNS > Edit, for `espresso.gg` (prod's custom domain)
#
# Then create each environment's `.tfvars` (never pushed to Github). For the
# secrets' Key Vault, `dev.tfvars` and `prod.tfvars`:
#
#   environment = "dev"
#
#   environment = "prod"
#
# For the site assets bucket, `dev.tfvars` and `prod.tfvars`:
#
#   environment = "dev"
#   account_id  = "<Cloudflare account ID>"
#
#   environment   = "prod"
#   account_id    = "<Cloudflare account ID>"
#   custom_domain = "assets.espresso.gg"
#   zone_id       = "<espresso.gg zone ID>"
#
# And export, for this script:
#
#   export CLOUDFLARE_API_TOKEN=<Terraform's Cloudflare API token>
#
# Optionally, `ARM_SUBSCRIPTION_ID` overrides the Azure CLI's selected
# subscription.

set -euo pipefail

environment="${1:-}"
if [[ "$environment" != "dev" && "$environment" != "prod" ]]; then
  echo "Usage: $0 dev|prod" >&2
  exit 1
fi

# Paths are relative to this script, wherever it's run from
cd "$(dirname "$0")"

step() { printf '\n==> %s\n' "$*"; }
fail() {
  echo "Error: $*" >&2
  exit 1
}

step "Checking prerequisites"
command -v terraform >/dev/null || fail "terraform is not installed"
command -v az >/dev/null || fail "the Azure CLI (az) is not installed, see this script's comments"
[[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || fail "CLOUDFLARE_API_TOKEN is not set"
for tfvars in "secrets/$environment.tfvars" "site_assets/$environment.tfvars"; do
  [[ -f "$tfvars" ]] || fail "$tfvars does not exist, see this script's comments"
  if grep -q '<' "$tfvars"; then
    fail "$tfvars still has placeholders, e.g. <Cloudflare account ID>"
  fi
done

step "Checking the Cloudflare API token's permissions"
# Terraform lists the account's token permission groups and creates the
# crawler's token, which both need "Account API Tokens" access
account_id="$(sed -n 's/^account_id *= *"\(.*\)"/\1/p' "site_assets/$environment.tfvars")"
if ! curl --silent --fail --output /dev/null \
  --header "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$account_id/tokens/permission_groups"; then
  echo "Edit the token (Manage Account > Account API Tokens), and add:" >&2
  echo "  Account > Account API Tokens > Edit" >&2
  fail "the Cloudflare API token can't access account $account_id's API tokens"
fi
echo "The token can manage account $account_id's API tokens"

step "Signing in to Azure"
# Terraform authenticates with the Azure CLI's session, no keys needed
az account show >/dev/null 2>&1 || az login
if [[ -n "${ARM_SUBSCRIPTION_ID:-}" ]]; then
  az account set --subscription "$ARM_SUBSCRIPTION_ID"
fi
# Terraform's azurerm provider and backend read the subscription from this
ARM_SUBSCRIPTION_ID="$(az account show --query id --output tsv)"
export ARM_SUBSCRIPTION_ID
echo "Using subscription: $(az account show --query name --output tsv) ($ARM_SUBSCRIPTION_ID)"

step "Checking the subscription's resource providers"
# A new subscription has to be registered for each Azure service it uses, e.g.
# Microsoft.Storage for storage accounts, or creating one fails with a 409
# "MissingSubscriptionRegistration"
unregistered=()
for namespace in Microsoft.Storage Microsoft.KeyVault; do
  state="$(az provider show --namespace "$namespace" --query registrationState --output tsv)"
  echo "$namespace: $state"
  [[ "$state" == "Registered" ]] || unregistered+=("$namespace")
done
if ((${#unregistered[@]})); then
  read -rp "Register ${unregistered[*]} now (once per subscription, it can take a few minutes)? [y/N] " answer
  if [[ "$answer" != [yY]* ]]; then
    echo "Register them later with:" >&2
    for namespace in "${unregistered[@]}"; do
      echo "  az provider register --namespace $namespace --wait" >&2
    done
    echo "or in the Portal: Subscriptions > your subscription > Resource providers." >&2
    fail "the subscription isn't registered for: ${unregistered[*]}"
  fi
  for namespace in "${unregistered[@]}"; do
    echo "Registering $namespace..."
    az provider register --namespace "$namespace" --wait
  done
fi

step "Remote state storage (root/)"
# This state is local, as it creates the storage every other state is kept in:
# keep its `terraform.tfstate` safe (it's not pushed to Github)
terraform -chdir=root init -input=false
terraform -chdir=root apply

step "Application secrets' Key Vault, $environment (secrets/)"
terraform -chdir=secrets init -input=false
terraform -chdir=secrets workspace select -or-create "$environment"
terraform -chdir=secrets apply -var-file="$environment.tfvars"
key_vault="$(terraform -chdir=secrets output -raw key_vault_name)"

step "Checking your access to the Key Vault's secrets"
# Your role on the vault can take a few minutes to apply after it's created,
# until then reading or writing its secrets fails with a 403
for attempt in {1..30}; do
  if az keyvault secret list --vault-name "$key_vault" --output none 2>/dev/null; then
    echo "You can access $key_vault's secrets"
    break
  fi
  ((attempt < 30)) || fail "you still can't access $key_vault's secrets after 10 minutes, re-run this script later"
  echo "Waiting for your role on $key_vault to apply ($attempt/30)..."
  sleep 20
done

step "Site assets bucket, $environment (site_assets/)"
# Writes the crawler's R2 credentials into the Key Vault
terraform -chdir=site_assets init -input=false
terraform -chdir=site_assets workspace select -or-create "$environment"
terraform -chdir=site_assets apply -var-file="$environment.tfvars"

step "Done"
echo "Assets are served from: $(terraform -chdir=site_assets output -raw public_url)"
echo "Secrets are stored in Key Vault: $key_vault"
cat <<EOF

The crawler's (\`extracty\`) environment, e.g. to run it locally (secrets are
read from Key Vault when these run, so they're not printed here):

  export ASSETS_BUCKET=$(terraform -chdir=site_assets output -raw bucket_name)
  export R2_ACCOUNT_ID=<Cloudflare account ID>
  export R2_ACCESS_KEY_ID=\$(az keyvault secret show --vault-name $key_vault --name r2-access-key-id --query value --output tsv)
  export R2_SECRET_ACCESS_KEY=\$(az keyvault secret show --vault-name $key_vault --name r2-secret-access-key --query value --output tsv)
EOF
