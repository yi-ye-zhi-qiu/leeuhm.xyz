terraform {
  required_version = ">= 1.6"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=5.0.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "state-resource-group"
    storage_account_name = "espressoggtfstates"
    container_name       = "tf-states-storage"
    key                  = "site_assets.tfstate"
  }
}

provider "cloudflare" {}

# For the crawler's R2 credentials in Key Vault, with the Azure CLI (`az login`),
# in the subscription from `ARM_SUBSCRIPTION_ID`
provider "azurerm" {
  features {}
}
