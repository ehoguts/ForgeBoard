mock_provider "aws" {
  override_during = plan
  mock_data "aws_partition" {
    defaults = { partition = "aws" }
  }
  mock_resource "aws_secretsmanager_secret" {
    defaults = { arn = "arn:aws:secretsmanager:us-east-1:000000000000:secret:forgeboard-application-placeholder" }
  }
  mock_resource "aws_s3_bucket" {
    defaults = { arn = "arn:aws:s3:::forgeboard-placeholder-releases" }
  }
  mock_resource "aws_db_instance" {
    defaults = {
      master_user_secret = [{
        secret_arn    = "arn:aws:secretsmanager:us-east-1:000000000000:secret:master-placeholder"
        kms_key_id    = "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000"
        secret_status = "active"
      }]
    }
  }
}

variables {
  aws_account_id          = "000000000000"
  ami_id                  = "ami-00000000000000000"
  domain_name             = "forgeboard.example.com"
  postgres_engine_version = "16.16"
}

run "private_managed_database" {
  command = plan

  assert {
    condition     = aws_db_instance.app.publicly_accessible == false && aws_db_instance.app.storage_encrypted
    error_message = "PostgreSQL must remain private and encrypted."
  }
  assert {
    condition     = aws_db_instance.app.manage_master_user_password == true && aws_db_instance.app.password == null
    error_message = "RDS must manage its password; Terraform must not receive it."
  }
  assert {
    condition     = aws_db_instance.app.backup_retention_period == 7 && aws_db_instance.app.deletion_protection && !aws_db_instance.app.skip_final_snapshot
    error_message = "The reference DB must retain backups, deletion protection, and final snapshots."
  }
  assert {
    condition     = length(aws_subnet.database) == 2 && length(aws_route_table.database.route) == 0
    error_message = "Use two DB subnets without Internet/NAT routes."
  }
  assert {
    condition     = one(aws_db_parameter_group.app.parameter).name == "rds.force_ssl" && one(aws_db_parameter_group.app.parameter).value == "1"
    error_message = "Every database connection must require TLS."
  }
  assert {
    condition     = aws_vpc_security_group_ingress_rule.database_from_app.from_port == 5432 && aws_vpc_security_group_ingress_rule.database_from_app.cidr_ipv4 == null
    error_message = "Database access must use a security-group reference, never a public CIDR."
  }
}

run "instance_and_iam_contract" {
  command = plan

  assert {
    condition     = aws_instance.app.metadata_options[0].http_tokens == "required" && aws_instance.app.metadata_options[0].http_put_response_hop_limit == 1
    error_message = "Require IMDSv2 and prevent ordinary bridged containers reaching instance-role credentials."
  }
  assert {
    condition     = aws_instance.app.root_block_device[0].encrypted && aws_instance.app.credit_specification[0].cpu_credits == "standard"
    error_message = "Encrypt the root disk and avoid unlimited EC2 surplus-credit charges."
  }
  assert {
    condition     = alltrue([for rule in aws_vpc_security_group_ingress_rule.https : rule.from_port == 443 && rule.to_port == 443]) && alltrue([for rule in aws_vpc_security_group_ingress_rule.http_challenge : rule.from_port == 80 && rule.to_port == 80])
    error_message = "Only HTTPS and HTTP challenge ingress are intended; SSH is not allowed."
  }
  assert {
    condition     = toset(jsondecode(aws_iam_role_policy.app.policy).Statement[0].Action) == toset(["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"])
    error_message = "The runtime's secret access must be read-only."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.app.policy).Statement[0].Resource == aws_secretsmanager_secret.application_database.arn
    error_message = "The runtime may read only the app credential, never the RDS master secret."
  }
  assert {
    condition     = aws_secretsmanager_secret.application_database.recovery_window_in_days == 30
    error_message = "Application secret deletion must preserve a recovery window."
  }
  assert {
    condition     = aws_s3_bucket.releases.force_destroy == false && aws_s3_bucket_public_access_block.releases.restrict_public_buckets
    error_message = "Release history must not be public or automatically emptied during teardown."
  }
}

run "reject_account_id" {
  command = plan
  variables {
    aws_account_id = "wrong"
  }
  expect_failures = [var.aws_account_id]
}

run "reject_url_instead_of_domain" {
  command = plan
  variables {
    domain_name = "http://example.com/path"
  }
  expect_failures = [var.domain_name]
}

run "reject_other_major_postgres_version" {
  command = plan
  variables {
    postgres_engine_version = "17.1"
  }
  expect_failures = [var.postgres_engine_version]
}

run "reject_mismatched_availability_zones" {
  command = plan
  variables {
    availability_zones = ["eu-west-1a", "eu-west-1b"]
  }
  expect_failures = [aws_instance.app]
}
