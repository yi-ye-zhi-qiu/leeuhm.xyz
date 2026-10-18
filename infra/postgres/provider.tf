# https://neon.com/docs/reference/terraform
terraform {
  required_version = ">= 1.5"

  required_providers {
    neon = { source = "kislerdm/neon" }
  }

  # TODO: connect to Azure remote state storage
}

# Authenticates via the NEON_API_KEY environment variable.
provider "neon" {}
