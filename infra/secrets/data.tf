# Whoever runs Terraform, i.e. the Azure CLI's signed in user
data "azurerm_client_config" "this" {}
