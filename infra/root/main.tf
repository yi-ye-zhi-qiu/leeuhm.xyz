resource "azurerm_resource_group" "this" {
  name     = "state-resource-group"
  location = "East US"
}

resource "azurerm_storage_account" "this" {
  # 3-24 lowercase letters and numbers, unique across all of Azure
  name                     = "espressoggtfstates"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "this" {
  name                  = "tf-states-storage"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}
