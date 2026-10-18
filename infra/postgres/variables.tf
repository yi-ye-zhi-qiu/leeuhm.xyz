variable "project_name" {
  type    = string
  default = "ancient-phi"
}

variable "neon_region" {
  type        = string
  default     = "aws-us-east-1"
  description = "Neon region id (e.g. aws-us-east-1, aws-us-east-2)."
}

variable "pg_version" {
  type    = number
  default = 16
}

variable "database_name" {
  type    = string
  default = ""
}

variable "role_name" {
  type    = string
  default = ""
}

variable "history_retention_seconds" {
  type        = number
  default     = 21600
  description = "Point-in-time restore window. Free-tier max is 21600 (6h); raise on paid plans."
}
