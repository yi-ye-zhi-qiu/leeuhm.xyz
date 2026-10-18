# e.g. `terraform output -raw writer_secret_access_key` for sensitive outputs

output "bucket_name" {
  description = "The crawler's `ASSETS_BUCKET`."
  value       = cloudflare_r2_bucket.assets.name
}

output "public_url" {
  description = "Base URL the frontend loads assets from, e.g. `{public_url}/item/3158.png`."
  value = (
    var.custom_domain == null
    ? "https://${cloudflare_r2_managed_domain.assets.domain}"
    : "https://${var.custom_domain}"
  )
}

output "s3_endpoint" {
  description = "S3 API endpoint of the account's R2 buckets, i.e. `R2_ENDPOINT_URL`."
  value       = "https://${var.account_id}.r2.cloudflarestorage.com"
}

# R2's S3 credentials of an API token are its id and the SHA-256 of its value,
# see https://developers.cloudflare.com/r2/api/tokens/#get-s3-api-credentials-from-an-api-token
output "writer_access_key_id" {
  description = "The crawler's `R2_ACCESS_KEY_ID`."
  value       = cloudflare_api_token.writer.id
  sensitive   = true
}

output "writer_secret_access_key" {
  description = "The crawler's `R2_SECRET_ACCESS_KEY`."
  value       = sha256(cloudflare_api_token.writer.value)
  sensitive   = true
}
