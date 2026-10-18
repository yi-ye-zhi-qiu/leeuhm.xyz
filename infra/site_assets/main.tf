# Storage of frontend assets like champion icons, skill icons,
# so on and so forth.
#
# Assets are public: the frontend loads them over HTTPS from `public_url`
# (e.g. `https://assets.espresso.gg/item/3158.png`) without any credentials. Only
# the crawler writes to the bucket, with a token scoped to it.

resource "cloudflare_r2_bucket" "this" {
  account_id = var.account_id
  name       = local.bucket_name
  location   = var.bucket_location
}

# Public read access, at either a custom domain (cached by Cloudflare's CDN) or,
# without one, the bucket's rate limited `pub-<hash>.r2.dev` domain
resource "cloudflare_r2_custom_domain" "this" {
  count = var.custom_domain == null ? 0 : 1

  account_id  = var.account_id
  bucket_name = cloudflare_r2_bucket.this.name
  domain      = var.custom_domain
  zone_id     = var.zone_id
  enabled     = true
  min_tls     = "1.2"
}

resource "cloudflare_r2_managed_domain" "this" {
  account_id  = var.account_id
  bucket_name = cloudflare_r2_bucket.this.name
  enabled     = var.custom_domain == null
}

# Read & write access to this bucket's objects (only), for the crawler. Its S3
# credentials are stored in Key Vault, below. It's owned by the account rather
# than a user, so it outlives any one user's access.
resource "cloudflare_account_token" "this" {
  account_id = var.account_id
  name       = "${local.bucket_name}-writer"

  policies = [{
    effect            = "allow"
    permission_groups = [{ id = local.r2_object_write_permission_id }]
    # A single bucket, `com.cloudflare.edge.r2.bucket.<account>_<jurisdiction>_<bucket>`
    resources = jsonencode({
      "com.cloudflare.edge.r2.bucket.${var.account_id}_default_${cloudflare_r2_bucket.this.name}" = "*"
    })
  }]
}

# The writer token's S3 credentials, read by the crawler as `R2_ACCESS_KEY_ID`
# and `R2_SECRET_ACCESS_KEY`. They're its id and the SHA-256 of its value, see
# https://developers.cloudflare.com/r2/api/tokens/#get-s3-api-credentials-from-an-api-token
resource "azurerm_key_vault_secret" "r2_access_key_id" {
  key_vault_id = data.azurerm_key_vault.this.id
  name         = "r2-access-key-id"
  value        = cloudflare_account_token.this.id
}

resource "azurerm_key_vault_secret" "r2_secret_access_key" {
  key_vault_id = data.azurerm_key_vault.this.id
  name         = "r2-secret-access-key"
  value        = sha256(cloudflare_account_token.this.value)
}
