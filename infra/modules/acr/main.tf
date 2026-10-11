locals {
  app = var.append_workspace ? "${var.app}${title(terraform.workspace)}" : var.app
}


resource "azurerm_container_registry" "acr" {
  # Add as AZURE_REGISTRY (repository secret) for CI/CD
  # Identical to below CLI command:
  # az acr show --name $ACR_NAME --query "id"
  name                = local.app
  resource_group_name = var.resource_group_name
  location            = var.resource_group_location
  sku                 = "Basic"
  admin_enabled       = true
}

