resource "aws_s3_bucket" "this" {
  bucket = "leeuhmdata"
  bucket_namespace = "account-regional"
}
