# simple dev/prod sdlc with terraform workspace navigation between them
# for more complex data branching, we can do that:
# https://neon.com/docs/reference/terraform

resource "neon_project" "this" {
  name       = var.project_name
  region_id  = var.neon_region
  pg_version = var.pg_version

  # Free-tier caps this at 21600s (6h); the provider default of 86400 is rejected.
  history_retention_seconds = var.history_retention_seconds

  branch {
    name          = "prod"
    database_name = var.database_name
    role_name     = var.role_name
  }
}

# copy-on-write of prod
resource "neon_branch" "dev" {
  project_id = neon_project.this.id
  parent_id  = neon_project.this.default_branch_id
  name       = "dev"
}

resource "neon_endpoint" "dev" {
  project_id = neon_project.this.id
  branch_id  = neon_branch.dev.id
  type       = "read_write"
}

