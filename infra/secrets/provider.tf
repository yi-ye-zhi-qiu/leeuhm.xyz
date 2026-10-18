terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=5.0.0"
    }
  }

  # One state per workspace (environment)
  backend "azurerm" {
    resource_group_name  = "state-resource-group"
    storage_account_name = "espressoggtfstates"
    container_name       = "tf-states-storage"
    key                  = "secrets.tfstate"
  }
}

# Authenticates with the Azure CLI (`az login`), in the subscription from
# `ARM_SUBSCRIPTION_ID`
provider "azurerm" {
  features {}
}
