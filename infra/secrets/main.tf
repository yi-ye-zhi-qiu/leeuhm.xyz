resource "azurerm_resource_group" "this" {
  name     = "secrets-resource-group-${var.environment}"
  location = var.location
}

resource "azurerm_key_vault" "this" {
  # 3-24 letters, numbers and hyphens, unique across all of Azure. A deleted
  # vault's name stays reserved for `soft_delete_retention_days`.
  name                       = "espresso-gg-${var.environment}"
  resource_group_name        = azurerm_resource_group.this.name
  location                   = azurerm_resource_group.this.location
  tenant_id                  = data.azurerm_client_config.this.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  # Access is granted with Azure roles, e.g. "Key Vault Secrets User" for an
  # application's identity, rather than the vault's legacy access policies
  rbac_authorization_enabled = true
}

# Lets whoever runs Terraform read and write secrets, e.g. the crawler's R2
# credentials. Roles can take a few minutes to apply after this is created.
resource "azurerm_role_assignment" "this" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.this.object_id
}
