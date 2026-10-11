module "resource_group" {
  source = "../modules/resource-group"

  region = "East US 1"
  app    = "crawlerResourceGroup"
}

module "acr" {
  source = "../modules/acr"

  app                     = "crawlerAcr"
  resource_group_name     = module.resource_group.output.resource_group_name
  resource_group_location = module.resource_group.output.resource_group_location
}

module "networking" {
  source = "../modules/network"

  app                     = "crawlerNetwork"
  nat_gateway_zones       = ["2"]
  resource_group_name     = module.resource_group.output.resource_group_name
  resource_group_location = module.resource_group.output.resource_group_location
}

module "storage_container" {
  source = "../modules/storage-container"

  append_workspace        = false
  app                     = "crawlstorage"
  resource_group_name     = module.resource_group.output.resource_group_name
  resource_group_location = module.resource_group.output.resource_group_location
}

module "acs" {
  source = "../modules/acs"

  app                       = "crawlerTask"
  container_name            = "crawl-container-${terraform.workspace}"
  repository_login_server   = module.acr.output.repository_server
  repository_login_username = module.acr.output.repository_username
  repository_login_password = module.acr.output.repository_password
  resource_group_name       = module.resource_group.output.resource_group_name
  resource_group_location   = module.resource_group.output.resource_group_location
  # TODO: Replace the below with a config block
  image_name              = "crawler"
  image_tag               = "latest"
  azure_storage_container = module.storage_container.output.storage_container_name
  azure_account_url       = module.storage_container.output.storage_account_name
  azure_account_key       = module.storage_container.output.storage_account_primary_access_key
  network_profile_id      = module.networking.output.network_profile_id
}


# ================ CI/CD ============================================= #
# Below is everything required for CI of the crawler's Github repository:
# A Service Principal is an application within Azure Active Directory
# whose authentication tokens can be used as the client_id, client_secret,
# and tenant_id fields needed by Terraform.
resource "azuread_application" "app" {
  display_name = "app"
}

resource "azuread_service_principal" "app" {
  client_id = azuread_application.app.client_id
}

resource "azuread_application_password" "key" {
  application_id = azuread_application.app.id
}

# For our CI/CD pipeline, the service principal needs access to ACR.
# Ideally this would be in a separate repository.
# This is identical to the below CLI command:
# az role assignment create --assignee $SERVICE_PRINCIPAL_ID --scope $ACR_REGISTRY_ID --role acrpull
# It is borrowed from: https://learn.microsoft.com/en-us/azure/container-registry/container-registry-auth-service-principal
# You can verify through:
# docker login ${acr.azureco.io} --username ${client_id} --password ${app_password}
resource "azurerm_role_assignment" "appServiceAcrPush" {
  scope                = data.azurerm_subscription.primary.id
  role_definition_name = "AcrPush"
  principal_id         = azuread_service_principal.app.object_id
}
# ================= CI/CD -------------=============================== #
