# Storage of frontend assets like champion icons, skill icons,
# so on and so forth, see `backend/extracty/spiders/community_dragon.py`.
#
# Assets are public: the frontend loads them over HTTPS from `public_url`
# (e.g. `https://assets.leeuhm.xyz/item/3158.png`) without any credentials. Only
# the crawler writes to the bucket, with a token scoped to it.

locals {
  bucket_name = "leeuhmxyz-assets-${var.environment}"
}

resource "cloudflare_r2_bucket" "assets" {
  account_id = var.account_id
  name       = local.bucket_name
  location   = var.bucket_location
}

# Public read access, at either a custom domain (cached by Cloudflare's CDN) or,
# without one, the bucket's rate limited `pub-<hash>.r2.dev` domain
resource "cloudflare_r2_custom_domain" "assets" {
  count = var.custom_domain == null ? 0 : 1

  account_id  = var.account_id
  bucket_name = cloudflare_r2_bucket.assets.name
  domain      = var.custom_domain
  zone_id     = var.zone_id
  enabled     = true
  min_tls     = "1.2"
}

resource "cloudflare_r2_managed_domain" "assets" {
  account_id  = var.account_id
  bucket_name = cloudflare_r2_bucket.assets.name
  enabled     = var.custom_domain == null
}

# Read & write access to this bucket's objects (only), for the crawler's
# `AssetStorePipeline`. Its S3 credentials are outputs, see `outputs.tf`.
data "cloudflare_api_token_permission_groups_list" "all" {}

locals {
  r2_object_write_permission_id = one([
    for group in data.cloudflare_api_token_permission_groups_list.all.result :
    group.id if group.name == "Workers R2 Storage Bucket Item Write"
  ])
}

resource "cloudflare_api_token" "writer" {
  name = "${local.bucket_name}-writer"

  policies = [{
    effect            = "allow"
    permission_groups = [{ id = local.r2_object_write_permission_id }]
    # A single bucket, `com.cloudflare.edge.r2.bucket.<account>_<jurisdiction>_<bucket>`
    resources = jsonencode({
      "com.cloudflare.edge.r2.bucket.${var.account_id}_default_${cloudflare_r2_bucket.assets.name}" = "*"
    })
  }]
}
