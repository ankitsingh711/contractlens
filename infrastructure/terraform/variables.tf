# Input variables. Defaults are chosen for a low-cost, portfolio-scale
# deployment (one small RDS instance, one small Redis node, Fargate tasks
# with minimal CPU/memory) — bump sizing via terraform.tfvars for anything
# resembling real traffic.

variable "project_name" {
  description = "Short name used to prefix/tag all resources."
  type        = string
  default     = "contractlens"
}

variable "environment" {
  description = "Deployment environment name (e.g. staging, production). Used in resource names/tags."
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread subnets across. Minimum 2 for RDS/ALB multi-AZ requirements."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "single_nat_gateway" {
  description = "If true, use one NAT gateway shared across all private subnets (cheaper). If false, one NAT gateway per AZ (more resilient, ~2x NAT cost). Portfolio default: true."
  type        = bool
  default     = true
}

# ---------------------------------------------------------------------------
# ECS / Fargate sizing
# ---------------------------------------------------------------------------

variable "api_cpu" {
  description = "Fargate task CPU units for the API service (1024 = 1 vCPU)."
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Fargate task memory (MiB) for the API service."
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired running task count for the API service."
  type        = number
  default     = 2
}

variable "web_cpu" {
  description = "Fargate task CPU units for the web service (1024 = 1 vCPU)."
  type        = number
  default     = 256
}

variable "web_memory" {
  description = "Fargate task memory (MiB) for the web service."
  type        = number
  default     = 512
}

variable "web_desired_count" {
  description = "Desired running task count for the web service."
  type        = number
  default     = 2
}

variable "api_image_tag" {
  description = "Image tag in ECR to deploy for the api service (e.g. a git SHA). Defaults to 'latest' for the initial apply; CI should pass an explicit tag on every deploy."
  type        = string
  default     = "latest"
}

variable "web_image_tag" {
  description = "Image tag in ECR to deploy for the web service."
  type        = string
  default     = "latest"
}

# ---------------------------------------------------------------------------
# RDS
# ---------------------------------------------------------------------------

variable "db_engine_version" {
  description = "PostgreSQL engine version. Must be 15+ for pgvector support on RDS."
  type        = string
  default     = "16.4"
}

variable "db_instance_class" {
  description = "RDS instance class. db.t4g.micro is enough for a portfolio-scale demo corpus; size up for real traffic."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage (GB) for RDS."
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Upper bound (GB) for RDS storage autoscaling."
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Default database name."
  type        = string
  default     = "contractlens"
}

variable "db_username" {
  description = "Master username for RDS. Password is generated and stored in Secrets Manager, not set here."
  type        = string
  default     = "contractlens"
}

variable "db_multi_az" {
  description = "Whether to enable Multi-AZ for RDS. Off by default to keep portfolio cost down; the target-state architecture diagram (docs/architecture.md) calls for Multi-AZ in a real production deployment — flip this to true there."
  type        = bool
  default     = false
}

variable "db_backup_retention_days" {
  description = "Automated backup retention period, in days."
  type        = number
  default     = 7
}

# ---------------------------------------------------------------------------
# ElastiCache (Redis)
# ---------------------------------------------------------------------------

variable "redis_node_type" {
  description = "ElastiCache node type. This app's Redis usage today is rate-limit counters (small INCR/EXPIRE keys) plus a planned task queue — not a high-memory workload, so a small burstable node is appropriate rather than over-provisioning."
  type        = string
  default     = "cache.t4g.micro"
}

variable "redis_engine_version" {
  description = "Redis engine version."
  type        = string
  default     = "7.1"
}

# ---------------------------------------------------------------------------
# S3
# ---------------------------------------------------------------------------

variable "document_bucket_force_destroy" {
  description = "If true, allows Terraform to delete the document bucket even if it still contains objects. Leave false in real production use; true is convenient for a portfolio demo teardown."
  type        = bool
  default     = false
}

# ---------------------------------------------------------------------------
# Secrets (sensitive — leave unset locally; inject via CI/CD secret store,
# environment variables (TF_VAR_...), or a .auto.tfvars file that is
# git-ignored. Never commit real values.)
# ---------------------------------------------------------------------------

variable "app_secret_key" {
  description = "Value for the API's SECRET_KEY (JWT signing). If left empty, a random one is generated by Terraform (random_password) and stored in Secrets Manager — fine for a first deploy, but note it will rotate on any apply that recreates the resource unless you pin it."
  type        = string
  default     = ""
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key, stored in Secrets Manager. Leave blank to deploy in demo/mock mode (LLM_PROVIDER=mock) with no key configured."
  type        = string
  default     = ""
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key, stored in Secrets Manager. Leave blank to deploy in demo/mock mode."
  type        = string
  default     = ""
  sensitive   = true
}

variable "cohere_api_key" {
  description = "Cohere API key (reranker), stored in Secrets Manager. Leave blank to use the mock reranker."
  type        = string
  default     = ""
  sensitive   = true
}

variable "langfuse_public_key" {
  description = "Langfuse public key for LLM trace observability (optional — StructuredLogObservability is the zero-config default)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key (optional)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "domain_name" {
  description = "Optional custom domain name to associate with CloudFront (requires an ACM certificate in us-east-1). Leave blank to use the default *.cloudfront.net domain."
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN (must be in us-east-1 for CloudFront) for var.domain_name. Required only if domain_name is set."
  type        = string
  default     = ""
}
