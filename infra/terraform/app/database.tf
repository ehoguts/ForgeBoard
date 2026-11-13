resource "aws_db_subnet_group" "app" {
  name       = "${local.name}-private"
  subnet_ids = [for subnet in aws_subnet.database : subnet.id]
  tags       = { Name = "${local.name}-private" }
}

resource "aws_db_parameter_group" "app" {
  name_prefix = "${local.name}-"
  family      = "postgres16"
  description = "Require TLS for every database connection."
  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "pending-reboot"
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_instance" "app" {
  identifier                      = "${local.name}-postgres"
  engine                          = "postgres"
  engine_version                  = var.postgres_engine_version
  instance_class                  = var.database_instance_class
  allocated_storage               = 20
  max_allocated_storage           = 20
  storage_type                    = "gp3"
  storage_encrypted               = true
  db_name                         = var.database_name
  username                        = "forgeboard_admin"
  manage_master_user_password     = true
  port                            = 5432
  db_subnet_group_name            = aws_db_subnet_group.app.name
  vpc_security_group_ids          = [aws_security_group.database.id]
  parameter_group_name            = aws_db_parameter_group.app.name
  publicly_accessible             = false
  multi_az                        = false
  auto_minor_version_upgrade      = true
  allow_major_version_upgrade     = false
  apply_immediately               = false
  backup_retention_period         = 7
  backup_window                   = "03:00-04:00"
  maintenance_window              = "sun:04:00-sun:05:00"
  deletion_protection             = var.database_deletion_protection
  skip_final_snapshot             = false
  final_snapshot_identifier       = "${local.name}-final-${var.final_snapshot_suffix}"
  delete_automated_backups        = false
  copy_tags_to_snapshot           = true
  performance_insights_enabled    = false
  monitoring_interval             = 0
  enabled_cloudwatch_logs_exports = []
  tags                            = { Name = "${local.name}-postgres" }
}

# Only secret metadata is managed by Terraform. The operator populates SecretString
# through a future, separately authorized operator bootstrap process. No password
# or DATABASE_URL is configured in Terraform or deliberately written to its state.
resource "aws_secretsmanager_secret" "application_database" {
  name                    = "${local.name}/application-database"
  description             = "Least-privilege ForgeBoard database credentials; populated outside Terraform."
  recovery_window_in_days = 30
  tags                    = { Name = "${local.name}-application-database" }
}
