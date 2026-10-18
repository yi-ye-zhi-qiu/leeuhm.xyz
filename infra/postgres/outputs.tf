output "project_id" {
  value = neon_project.this.id
}

output "prod_connection_uri" {
  value     = neon_project.this.connection_uri
  sensitive = true
}

output "dev_connection_uri" {
  value     = "postgresql://${neon_project.this.database_user}:${neon_project.this.database_password}@${neon_endpoint.dev.host}/${neon_project.this.database_name}?sslmode=require"
  sensitive = true
}
