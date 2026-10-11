terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "3.0.1"
    }
  }
  backend "azurerm" {
    resource_group_name  = "stateResourceGroup"
    storage_account_name = "tf-states"
    container_name       = "tf-states-storage"
    key                  = "crawl.tfstate"
  }

}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}
