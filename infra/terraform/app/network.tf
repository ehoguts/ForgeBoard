resource "aws_vpc" "app" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = local.name }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.app.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 1)
  availability_zone       = var.availability_zones[0]
  map_public_ip_on_launch = false
  tags                    = { Name = "${local.name}-app-public" }
}

resource "aws_subnet" "database" {
  for_each                = { for index, zone in var.availability_zones : zone => index }
  vpc_id                  = aws_vpc.app.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 20 + each.value)
  availability_zone       = each.key
  map_public_ip_on_launch = false
  tags                    = { Name = "${local.name}-db-${each.value}" }
}

resource "aws_internet_gateway" "app" {
  vpc_id = aws_vpc.app.id
  tags   = { Name = local.name }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.app.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.app.id
  }
  tags = { Name = "${local.name}-public" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Explicitly associate private DB subnets with a route table without IGW/NAT routes.
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.app.id
  route  = []
  tags   = { Name = "${local.name}-db-private" }
}

resource "aws_route_table_association" "database" {
  for_each       = aws_subnet.database
  subnet_id      = each.value.id
  route_table_id = aws_route_table.database.id
}

resource "aws_security_group" "app" {
  name_prefix            = "${local.name}-app-"
  description            = "Only HTTP ACME and HTTPS public ingress; administration uses SSM."
  vpc_id                 = aws_vpc.app.id
  revoke_rules_on_delete = true
  tags                   = { Name = "${local.name}-app" }
}

resource "aws_security_group" "database" {
  name_prefix            = "${local.name}-database-"
  description            = "Private PostgreSQL, reachable only from the app security group."
  vpc_id                 = aws_vpc.app.id
  revoke_rules_on_delete = true
  tags                   = { Name = "${local.name}-database" }
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  for_each          = var.web_ingress_cidrs
  security_group_id = aws_security_group.app.id
  description       = "HTTPS application traffic"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_ingress_rule" "http_challenge" {
  for_each          = var.web_ingress_cidrs
  security_group_id = aws_security_group.app.id
  description       = "ACME HTTP challenge and redirect to HTTPS"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "database_from_app" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_security_group.app.id
  description                  = "PostgreSQL from the single app host only"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.app.id
  description       = "Signed package repositories, AWS APIs, and ACME"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_vpc_security_group_egress_rule" "database" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.database.id
  description                  = "TLS PostgreSQL to the private DB"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "dns_udp" {
  security_group_id = aws_security_group.app.id
  description       = "VPC DNS resolver"
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "udp"
  from_port         = 53
  to_port           = 53
}

resource "aws_vpc_security_group_egress_rule" "dns_tcp" {
  security_group_id = aws_security_group.app.id
  description       = "VPC DNS resolver TCP fallback"
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "tcp"
  from_port         = 53
  to_port           = 53
}
