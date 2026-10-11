resource "azurerm_resource_group" "tfstate" {
  name     = "stateResourceGroup"
  location = "East US 1"
}

resource "azurerm_storage_account" "storage_acc" {
  name                     = "tf-states"
  resource_group_name      = azurerm_resource_group.tfstate.name
  location                 = azurerm_resource_group.tfstate.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "storage_container" {
  name                  = "tf-states-storage"
  storage_account_name  = azurerm_storage_account.storage_acc.name
  container_access_type = "private"
}
