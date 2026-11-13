output "instance_id" {
  value       = aws_instance.app.id
  description = "SSM-managed host; no SSH ingress or SSH key is configured."
}

output "instance_role_name" {
  value = aws_iam_role.app.name
}

output "public_ip" {
  value       = aws_eip.app.public_ip
  description = "Publish an A record for domain_name only after the approved deployment."
}

output "dns_records" {
  value = [{ name = var.domain_name, type = "A", value = aws_eip.app.public_ip }]
}

output "app_origin" {
  value = "https://${var.domain_name}"
}

output "db_endpoint" {
  value       = aws_db_instance.app.address
  description = "Private RDS hostname. Clients must use TLS verify-full with the AWS RDS CA bundle."
}

output "db_name" {
  value = aws_db_instance.app.db_name
}

output "app_secret_arn" {
  value       = aws_secretsmanager_secret.application_database.arn
  description = "Secret metadata only; populate with the least-privilege app role before deployment."
}

output "master_secret_arn" {
  value       = aws_db_instance.app.master_user_secret[0].secret_arn
  description = "Operator bootstrap only. The EC2 instance IAM policy cannot read this secret."
}

output "release_bucket_name" {
  value = aws_s3_bucket.releases.id
}

output "release_prefix" {
  value = "releases/"
}
