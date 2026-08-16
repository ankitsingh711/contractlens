# Secrets Manager — everything the API's app/core/config.py treats as
# sensitive (SECRET_KEY, DB credentials, LLM/embedding/reranker provider
# keys, Langfuse keys) lives here, never as plaintext container
# environment variables in the ECS task definition. ecs.tf references these
# ARNs via the task definition's `secrets` block (resolved by the ECS agent
# at container start, injected into the container's env — the API code
# itself needs no changes, it just reads os.environ / pydantic-settings as
# it already does).

resource "random_password" "db_password" {
  length  = 32
  special = false # avoid characters that need URL-encoding in DATABASE_URL
}

resource "random_password" "generated_secret_key" {
  length  = 64
  special = false
}

locals {
  # Use the operator-supplied SECRET_KEY if one was passed via
  # var.app_secret_key, otherwise fall back to a generated one so a first
  # `terraform apply` doesn't hard-fail on a missing secret.
  app_secret_key = var.app_secret_key != "" ? var.app_secret_key : random_password.generated_secret_key.result
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${local.name}/db-credentials"
  description = "RDS master credentials for ${local.name}"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    # Full DATABASE_URL in the async-SQLAlchemy driver form config.py expects.
    database_url = "postgresql+asyncpg://${var.db_username}:${random_password.db_password.result}@${aws_db_instance.main.address}:5432/${var.db_name}"
  })
}

resource "aws_secretsmanager_secret" "app_secret_key" {
  name        = "${local.name}/app-secret-key"
  description = "SECRET_KEY used for JWT signing (app/core/config.py)"
}

resource "aws_secretsmanager_secret_version" "app_secret_key" {
  secret_id     = aws_secretsmanager_secret.app_secret_key.id
  secret_string = local.app_secret_key
}

# LLM / embedding / reranker provider keys. Empty string is a valid value —
# it just means that provider stays on its mock/demo implementation
# (LLM_PROVIDER=mock etc.), same as local dev with no .env keys set.
resource "aws_secretsmanager_secret" "provider_keys" {
  name        = "${local.name}/provider-keys"
  description = "OpenAI/Anthropic/Cohere/Langfuse API keys. To add a new provider key: add it to the jsonencode() below and reference the new key in ecs.tf's secrets block — same pattern, no other plumbing needed."
}

resource "aws_secretsmanager_secret_version" "provider_keys" {
  secret_id = aws_secretsmanager_secret.provider_keys.id
  secret_string = jsonencode({
    openai_api_key      = var.openai_api_key
    anthropic_api_key   = var.anthropic_api_key
    cohere_api_key      = var.cohere_api_key
    langfuse_public_key = var.langfuse_public_key
    langfuse_secret_key = var.langfuse_secret_key
  })
}
