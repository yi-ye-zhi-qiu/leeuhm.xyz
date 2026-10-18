terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=5.0.0"
    }
  }
}

# Authenticates with the Azure CLI (`az login`), in the subscription from
# `ARM_SUBSCRIPTION_ID`. This state is local: it creates the storage every other
# state is kept in.
provider "azurerm" {
  features {}
}
