# ECS cluster on Fargate (no EC2 instances to manage) running two services:
# api (FastAPI) and web (Next.js). See docs/architecture.md §12 for why
# Fargate: no server fleet to patch/size for a two-service, portfolio-scale
# app, and both images are already plain Docker builds with no GPU/special
# kernel requirement that would push toward EKS or self-managed EC2.

resource "aws_ecs_cluster" "main" {
  name = "${local.name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = "${local.name}-cluster" }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name}/api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "web" {
  name              = "/ecs/${local.name}/web"
  retention_in_days = 30
}

# --- API task definition ----------------------------------------------------

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task_api.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
      essential = true
      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]
      environment = [
        { name = "ENV", value = var.environment },
        { name = "DEBUG", value = "false" },
        { name = "STORAGE_BACKEND", value = "s3" },
        { name = "S3_BUCKET", value = aws_s3_bucket.documents.bucket },
        { name = "S3_REGION", value = var.aws_region },
        # Redis has transit encryption enabled (elasticache.tf) -> rediss://.
        { name = "REDIS_URL", value = "rediss://${aws_elasticache_replication_group.main.primary_endpoint_address}:6379/0" },
        { name = "PROMPTS_DIR", value = "/app/prompts" },
        { name = "EVALUATION_DATASET_DIR", value = "/evaluation/datasets" },
        { name = "CORS_ORIGINS", value = jsonencode(["https://${var.domain_name != "" ? var.domain_name : aws_cloudfront_distribution.main.domain_name}"]) },
        { name = "LLM_PROVIDER", value = var.openai_api_key != "" ? "openai" : "mock" },
        { name = "EMBEDDING_PROVIDER", value = var.openai_api_key != "" ? "openai" : "mock" },
        { name = "RERANKER_PROVIDER", value = var.cohere_api_key != "" ? "cohere" : "mock" },
      ]
      secrets = [
        { name = "SECRET_KEY", valueFrom = aws_secretsmanager_secret.app_secret_key.arn },
        { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:database_url::" },
        { name = "OPENAI_API_KEY", valueFrom = "${aws_secretsmanager_secret.provider_keys.arn}:openai_api_key::" },
        { name = "ANTHROPIC_API_KEY", valueFrom = "${aws_secretsmanager_secret.provider_keys.arn}:anthropic_api_key::" },
        { name = "COHERE_API_KEY", valueFrom = "${aws_secretsmanager_secret.provider_keys.arn}:cohere_api_key::" },
        { name = "LANGFUSE_PUBLIC_KEY", valueFrom = "${aws_secretsmanager_secret.provider_keys.arn}:langfuse_public_key::" },
        { name = "LANGFUSE_SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.provider_keys.arn}:langfuse_secret_key::" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
    }
  ])

  tags = { Name = "${local.name}-api-taskdef" }
}

resource "aws_ecs_service" "api" {
  name            = "${local.name}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.app[*].id
    security_groups = [aws_security_group.ecs_api.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  enable_execute_command             = true # allows `aws ecs execute-command` for one-off debugging/migrations (e.g. running alembic upgrade head, CREATE EXTENSION vector)

  depends_on = [aws_lb_listener_rule.api]

  tags = { Name = "${local.name}-api-service" }
}

# --- Web task definition ----------------------------------------------------

resource "aws_ecs_task_definition" "web" {
  family                   = "${local.name}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.web_cpu
  memory                   = var.web_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  # No task role: the web container never calls AWS APIs directly (talks to
  # the API over REST only — see iam.tf).

  container_definitions = jsonencode([
    {
      name      = "web"
      image     = "${aws_ecr_repository.web.repository_url}:${var.web_image_tag}"
      essential = true
      portMappings = [
        { containerPort = 3000, protocol = "tcp" }
      ]
      environment = [
        # Baked in at image build time too (see apps/web/Dockerfile's
        # NEXT_PUBLIC_API_URL build arg) since it's a NEXT_PUBLIC_ var
        # inlined into the client bundle; set here as well for consistency
        # /any server-side usage.
        { name = "NEXT_PUBLIC_API_URL", value = "https://${var.domain_name != "" ? var.domain_name : aws_cloudfront_distribution.main.domain_name}/api" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.web.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "web"
        }
      }
    }
  ])

  tags = { Name = "${local.name}-web-taskdef" }
}

resource "aws_ecs_service" "web" {
  name            = "${local.name}-web"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = var.web_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.app[*].id
    security_groups = [aws_security_group.ecs_web.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web.arn
    container_name   = "web"
    container_port   = 3000
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  depends_on = [aws_lb_listener.http]

  tags = { Name = "${local.name}-web-service" }
}
