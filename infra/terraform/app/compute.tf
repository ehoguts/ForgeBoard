resource "aws_instance" "app" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name
  associate_public_ip_address = true
  monitoring                  = false
  user_data                   = file("${path.module}/bootstrap-host.sh")
  user_data_replace_on_change = true
  depends_on                  = [aws_route_table_association.public, aws_iam_role_policy.app]

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gib
    encrypted             = true
    delete_on_termination = true
  }

  credit_specification {
    cpu_credits = "standard"
  }

  lifecycle {
    precondition {
      condition     = alltrue([for zone in var.availability_zones : startswith(zone, var.aws_region)])
      error_message = "availability_zones must belong to aws_region."
    }
  }

  tags = { Name = "${local.name}-app" }
}

resource "aws_eip" "app" {
  domain = "vpc"
  tags   = { Name = "${local.name}-https" }
}

resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app.id
  depends_on    = [aws_internet_gateway.app, aws_route_table_association.public]
}
