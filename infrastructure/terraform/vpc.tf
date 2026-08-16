# VPC with public subnets (ALB, NAT gateways), private "app" subnets (ECS
# tasks), and private "data" subnets (RDS, ElastiCache) across >= 2 AZs.
# Security groups are per-tier with least-privilege ingress: each tier only
# accepts traffic from the specific security group in front of it, never
# 0.0.0.0/0 except the ALB's public HTTP(S) listener.

locals {
  az_count = length(var.availability_zones)
  name     = "${var.project_name}-${var.environment}"
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${local.name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name}-igw" }
}

# --- Subnets ---------------------------------------------------------------
# /24s carved out of the /16: public 0-9, app (private) 10-19, data (private) 20-29.

resource "aws_subnet" "public" {
  count                   = local.az_count
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "${local.name}-public-${var.availability_zones[count.index]}", Tier = "public" }
}

resource "aws_subnet" "app" {
  count             = local.az_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]

  tags = { Name = "${local.name}-app-${var.availability_zones[count.index]}", Tier = "app" }
}

resource "aws_subnet" "data" {
  count             = local.az_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 20)
  availability_zone = var.availability_zones[count.index]

  tags = { Name = "${local.name}-data-${var.availability_zones[count.index]}", Tier = "data" }
}

# --- NAT gateway(s) ----------------------------------------------------------
# ECS tasks in the app subnets need outbound internet (pull images via ECR's
# public API endpoints unless VPC endpoints are added, call out to
# OpenAI/Cohere/Langfuse). single_nat_gateway=true shares one NAT across all
# AZs to save cost (~$32/mo per extra NAT); set false for AZ-isolated
# resilience in a real production account.

resource "aws_eip" "nat" {
  count  = var.single_nat_gateway ? 1 : local.az_count
  domain = "vpc"
  tags   = { Name = "${local.name}-nat-eip-${count.index}" }
}

resource "aws_nat_gateway" "main" {
  count         = var.single_nat_gateway ? 1 : local.az_count
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  tags          = { Name = "${local.name}-nat-${count.index}" }

  depends_on = [aws_internet_gateway.main]
}

# --- Route tables ------------------------------------------------------------

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name}-public-rt" }
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public" {
  count          = local.az_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private route tables (one per AZ so each can point at its own NAT when
# single_nat_gateway=false; all point at NAT[0] when single_nat_gateway=true).

resource "aws_route_table" "private" {
  count  = local.az_count
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name}-private-rt-${count.index}" }
}

resource "aws_route" "private_nat" {
  count                  = local.az_count
  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
}

resource "aws_route_table_association" "app" {
  count          = local.az_count
  subnet_id      = aws_subnet.app[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "data" {
  count          = local.az_count
  subnet_id      = aws_subnet.data[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# --- Security groups ---------------------------------------------------------
# Tiered: internet -> alb_sg -> ecs_api_sg / ecs_web_sg -> rds_sg / redis_sg.
# Nothing but the ALB accepts ingress from 0.0.0.0/0.

resource "aws_security_group" "alb" {
  name        = "${local.name}-alb-sg"
  description = "ALB: public HTTP/HTTPS ingress, egress to ECS tasks only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from internet (redirected to HTTPS by listener)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "To ECS tasks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name}-alb-sg" }
}

resource "aws_security_group" "ecs_api" {
  name        = "${local.name}-ecs-api-sg"
  description = "API ECS tasks: ingress from ALB only, egress to RDS/Redis/internet (LLM providers)"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "From ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Outbound (RDS, Redis, ECR, S3, LLM/embedding/reranker providers, Langfuse)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name}-ecs-api-sg" }
}

resource "aws_security_group" "ecs_web" {
  name        = "${local.name}-ecs-web-sg"
  description = "Web ECS tasks: ingress from ALB only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "From ALB"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Outbound (ECR pulls, API calls at build/runtime)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name}-ecs-web-sg" }
}

resource "aws_security_group" "rds" {
  name        = "${local.name}-rds-sg"
  description = "RDS: ingress from the API's ECS tasks only, no public access"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres from API tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_api.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name}-rds-sg" }
}

resource "aws_security_group" "redis" {
  name        = "${local.name}-redis-sg"
  description = "ElastiCache: ingress from the API's ECS tasks only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from API tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_api.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name}-redis-sg" }
}
