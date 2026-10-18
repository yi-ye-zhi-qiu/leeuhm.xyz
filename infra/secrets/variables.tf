variable "environment" {
  description = "Deployment environment, part of resource names, e.g. `espresso-gg-dev`."
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be \"dev\" or \"prod\"."
  }
}

variable "location" {
  description = "Azure region of the vault."
  type        = string
  default     = "East US"
}
