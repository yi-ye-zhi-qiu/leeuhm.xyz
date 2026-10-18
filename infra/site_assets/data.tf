# The account's API token permission groups, e.g. "Workers R2 Storage Bucket
# Item Write"
data "cloudflare_account_api_token_permission_groups_list" "this" {
  account_id = var.account_id
}

# This environment's Key Vault, for the crawler's R2 credentials
data "azurerm_key_vault" "this" {
  name                = "espresso-gg-${var.environment}"
  resource_group_name = "secrets-resource-group-${var.environment}"
}
