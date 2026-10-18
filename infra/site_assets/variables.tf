variable "environment" {
  description = "Deployment environment, part of resource names, e.g. `leeuhmxyz-assets-dev`."
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be \"dev\" or \"prod\"."
  }
}

variable "account_id" {
  description = "Cloudflare account ID that owns the bucket, see the dashboard's account home."
  type        = string
}

variable "bucket_location" {
  description = "R2 location hint, one of \"apac\", \"eeur\", \"enam\", \"weur\", \"wnam\", \"oc\"."
  type        = string
  default     = "weur"
}

variable "custom_domain" {
  description = "Public domain serving the bucket, e.g. `assets.leeuhm.xyz`. When null, the rate limited `r2.dev` domain is used instead (fine for dev, not for prod)."
  type        = string
  default     = null
}

variable "zone_id" {
  description = "Cloudflare zone ID of `custom_domain`'s DNS zone, e.g. `leeuhm.xyz`. Required with `custom_domain`."
  type        = string
  default     = null
}
