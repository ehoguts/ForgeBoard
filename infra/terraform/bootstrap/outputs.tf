output "state_bucket_name" {
  value       = aws_s3_bucket.state.id
  description = "Bucket used by the application S3 backend and native .tflock locking."
}

output "backend_configuration" {
  value = {
    bucket       = aws_s3_bucket.state.id
    key          = "forgeboard/portfolio/terraform.tfstate"
    region       = var.aws_region
    encrypt      = true
    use_lockfile = true
  }
  description = "Non-secret backend settings; authenticate through AWS SSO/environment, never backend files."
}
