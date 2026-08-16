# RDS PostgreSQL — replaces the local pgvector/pgvector:pg16 container.
# pgvector ships as a preloadable extension on RDS Postgres 15+; no special
# parameter group setting is required to make `CREATE EXTENSION vector`
# available (unlike e.g. TimescaleDB, it doesn't need
# shared_preload_libraries). It still needs to actually be *run* once
# against the database — see the note below.
#
# IMPORTANT — verified against this repo, not assumed: the app's Alembic
# migrations (apps/api/app/db/migrations/versions/) do NOT contain a
# `CREATE EXTENSION vector` statement. Locally this works because the
# pgvector/pgvector:pg16 Docker image's initdb bootstrap already has the
# extension created in the default database. On RDS that bootstrap doesn't
# happen automatically, so the extension must be created once, out of band,
# before the first `alembic upgrade head` against this database:
#
#     CREATE EXTENSION IF NOT EXISTS vector;
#
# This is a one-line, one-time, idempotent statement. Recommended fix
# upstream: add it as the first line of the earliest Alembic migration
# (op.execute("CREATE EXTENSION IF NOT EXISTS vector")) so `alembic upgrade
# head` is sufficient on any fresh Postgres 15+ target, RDS included — that
# is a one-line change to apps/api, out of scope for this Terraform-only
# phase. Until that lands, run the statement by hand (via a bastion,
# `aws ecs execute-command` into a running API task, or a local `psql`
# tunneled through SSM Session Manager port forwarding) as the first step
# after `terraform apply` and before running migrations.

resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db-subnets"
  subnet_ids = aws_subnet.data[*].id
  tags       = { Name = "${local.name}-db-subnets" }
}

resource "aws_db_parameter_group" "main" {
  name   = "${local.name}-pg16"
  family = "postgres16"

  # log_statement / connection logging kept at defaults; nothing here is
  # required for pgvector specifically. Present as the place to add
  # tuning (e.g. shared_buffers, max_connections) if this ever needs to
  # scale beyond the default instance-class values.
  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # log queries slower than 1s — cheap baseline observability
  }

  tags = { Name = "${local.name}-pg16" }
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name}-db"
  engine         = "postgres"
  engine_version = var.db_engine_version

  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.main.name
  parameter_group_name   = aws_db_parameter_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  multi_az                = var.db_multi_az
  backup_retention_period = var.db_backup_retention_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:30-mon:05:30"

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${local.name}-db-final" : null
  deletion_protection       = var.environment == "production"

  copy_tags_to_snapshot = true

  tags = { Name = "${local.name}-db" }
}
