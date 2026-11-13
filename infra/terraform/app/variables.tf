variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region; recalculate the documented price estimate if changed."
}

variable "aws_account_id" {
  type        = string
  description = "Intended AWS account; provider operations reject a different account."
  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "Supply the intended 12-digit account ID."
  }
}

variable "project_name" {
  type    = string
  default = "forgeboard"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,19}$", var.project_name))
    error_message = "Use 3-20 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "environment" {
  type    = string
  default = "portfolio"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,9}$", var.environment))
    error_message = "Use 2-10 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "domain_name" {
  type        = string
  description = "A real DNS name controlled by the operator; point its A record at public_ip before HTTPS issuance."
  validation {
    condition = (
      length(var.domain_name) <= 253 &&
      can(regex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$", var.domain_name)) &&
      alltrue([for label in split(".", var.domain_name) : length(label) <= 63]) &&
      can(regex("[a-z]", element(reverse(split(".", var.domain_name)), 0)))
    )
    error_message = "Use a lowercase DNS hostname, not a URL, IP address or wildcard."
  }
}

variable "ami_id" {
  type        = string
  description = "Reviewed x86_64 Amazon Linux 2023 AMI for this region. Resolve the official SSM parameter and record the result before planning."
  validation {
    condition     = can(regex("^ami-[0-9a-f]{17}$", var.ami_id))
    error_message = "Supply a reviewed AL2023 x86_64 AMI ID; there is no implicit latest-image selection."
  }
}

variable "instance_type" {
  type        = string
  default     = "t3.small"
  description = "x86_64 instance matching the release image architecture and price estimate."
  validation {
    condition     = contains(["t3.small", "t3.medium"], var.instance_type)
    error_message = "Supported x86_64 portfolio sizes are t3.small and t3.medium; review cost before increasing."
  }
}

variable "root_volume_size_gib" {
  type    = number
  default = 16
  validation {
    condition     = var.root_volume_size_gib >= 16 && var.root_volume_size_gib <= 64
    error_message = "Use 16-64 GiB; the cost estimate assumes 16."
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
  validation {
    condition     = can(cidrnetmask(var.vpc_cidr)) && can(cidrsubnet(var.vpc_cidr, 8, 20))
    error_message = "Supply a valid IPv4 VPC CIDR large enough for the derived subnets."
  }
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
  description = "Two available AZs in aws_region. RDS subnet groups require at least two; the DB remains Single-AZ."
  validation {
    condition     = length(var.availability_zones) == 2 && length(distinct(var.availability_zones)) == 2
    error_message = "Supply two distinct availability zones."
  }
}

variable "web_ingress_cidrs" {
  type        = set(string)
  default     = ["0.0.0.0/0"]
  description = "Public HTTP challenge and HTTPS clients only. Restrict for a private demo if an externally valid ACME challenge path remains available."
  validation {
    condition     = alltrue([for cidr in var.web_ingress_cidrs : can(cidrnetmask(cidr))])
    error_message = "Use valid IPv4 CIDR blocks."
  }
}

variable "database_name" {
  type    = string
  default = "forgeboard"
  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{0,62}$", var.database_name))
    error_message = "Use a PostgreSQL-compatible database name."
  }
}

variable "postgres_engine_version" {
  type        = string
  description = "PostgreSQL 16 minor version confirmed available in the chosen RDS region; validate with describe-db-engine-versions before the approved plan."
  validation {
    condition     = can(regex("^16\\.[0-9]+$", var.postgres_engine_version))
    error_message = "Choose a supported PostgreSQL 16 minor release."
  }
}

variable "database_instance_class" {
  type    = string
  default = "db.t4g.micro"
  validation {
    condition     = contains(["db.t4g.micro", "db.t4g.small"], var.database_instance_class)
    error_message = "Supported portfolio sizes are db.t4g.micro and db.t4g.small; review cost before increasing."
  }
}

variable "database_deletion_protection" {
  type        = bool
  default     = true
  description = "Keep true normally. Disabling is an explicit prerequisite to an approved teardown."
}

variable "final_snapshot_suffix" {
  type        = string
  default     = "retained"
  description = "Use a unique suffix for each approved teardown; final snapshots are retained and incur storage charges."
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{0,24}$", var.final_snapshot_suffix))
    error_message = "Use 1-25 lowercase letters, digits or hyphens."
  }
}
