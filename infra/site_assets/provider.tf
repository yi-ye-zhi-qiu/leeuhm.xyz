terraform {
  required_version = ">= 1.6"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "state-resource-group"
    storage_account_name = "tf-states"
    container_name       = "tf-states-storage"
    key                  = "site_assets.tfstate"
  }
}

provider "cloudflare" {}
