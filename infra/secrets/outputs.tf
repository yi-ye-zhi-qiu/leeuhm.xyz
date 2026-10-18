output "key_vault_name" {
  description = "e.g. `az keyvault secret show --vault-name {key_vault_name} --name r2-access-key-id`."
  value       = azurerm_key_vault.this.name
}

output "key_vault_uri" {
  description = "For applications' Key Vault clients, e.g. `azure-keyvault-secrets`."
  value       = azurerm_key_vault.this.vault_uri
}
