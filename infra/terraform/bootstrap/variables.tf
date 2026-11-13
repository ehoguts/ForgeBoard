variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Region for the private remote-state bucket."
}

variable "aws_account_id" {
  type        = string
  description = "Explicit intended AWS account; the provider rejects a different account."
  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "aws_account_id must be the intended 12-digit AWS account ID."
  }
}

variable "state_bucket_name" {
  type        = string
  description = "Globally unique DNS-compatible bucket name. No credentials belong in this value."
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.state_bucket_name))
    error_message = "Use a 3-63 character lowercase bucket name containing only letters, digits and hyphens."
  }
}
