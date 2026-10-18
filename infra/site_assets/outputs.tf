output "bucket_name" {
  description = "The crawler's `ASSETS_BUCKET`."
  value       = cloudflare_r2_bucket.this.name
}

output "public_url" {
  description = "Base URL the frontend loads assets from, e.g. `{public_url}/item/3158.png`."
  value = (
    var.custom_domain == null
    ? "https://${cloudflare_r2_managed_domain.this.domain}"
    : "https://${var.custom_domain}"
  )
}

output "s3_endpoint" {
  description = "S3 API endpoint of the account's R2 buckets, i.e. `R2_ENDPOINT_URL`."
  value       = "https://${var.account_id}.r2.cloudflarestorage.com"
}
