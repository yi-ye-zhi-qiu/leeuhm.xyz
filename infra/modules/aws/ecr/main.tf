resource "aws_ecr_repository" "this" {
  provider = aws.ecr
  name = var.repository_name
}
