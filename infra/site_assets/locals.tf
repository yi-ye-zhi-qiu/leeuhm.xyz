locals {
  bucket_name = "espresso-assets-${var.environment}"

  # Permission to read & write a bucket's objects
  r2_object_write_permission_id = one([
    for group in data.cloudflare_account_api_token_permission_groups_list.this.result :
    group.id if group.name == "Workers R2 Storage Bucket Item Write"
  ])
}
