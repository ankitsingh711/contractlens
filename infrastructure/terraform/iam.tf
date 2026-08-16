# ECS IAM: two distinct roles per the standard ECS Fargate pattern.
#
# - execution role: used by the ECS agent itself (not app code) to pull
#   images from ECR, write container logs to CloudWatch, and resolve the
#   `secrets` block in the task definition. Same for both services.
# - task role (api only): assumed by the running api container's code —
#   this is the identity boto3 in app/services/storage/s3.py actually uses.
#   Scoped to only the one document bucket, nothing broader. The web
#   service gets no task role because it never talks to AWS directly (it
#   only calls the API over REST, per docs/architecture.md's "no shared
#   runtime" design).

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# --- Execution role (shared by both task definitions) -----------------------

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_execution_secrets" {
  statement {
    sid     = "ReadAppSecrets"
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.db_credentials.arn,
      aws_secretsmanager_secret.app_secret_key.arn,
      aws_secretsmanager_secret.provider_keys.arn,
    ]
  }
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name   = "${local.name}-ecs-execution-secrets"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.ecs_execution_secrets.json
}

# --- Task role (api service only) -------------------------------------------

resource "aws_iam_role" "ecs_task_api" {
  name               = "${local.name}-ecs-task-api"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json
}

data "aws_iam_policy_document" "api_task_s3" {
  statement {
    sid    = "DocumentBucketReadWrite"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["${aws_s3_bucket.documents.arn}/*"]
  }

  statement {
    sid       = "DocumentBucketList"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.documents.arn]
  }
}

resource "aws_iam_role_policy" "api_task_s3" {
  name   = "${local.name}-api-task-s3"
  role   = aws_iam_role.ecs_task_api.id
  policy = data.aws_iam_policy_document.api_task_s3.json
}

# CloudWatch Logs access for the app itself is not needed beyond what the
# execution role already grants for the `awslogs` driver — application code
# never calls CloudWatch APIs directly (it logs to stdout, per
# apps/api's structured logging setup, and the log driver ships that to
# CloudWatch). No additional task-role permissions are granted here —
# deliberately not AdministratorAccess or a wildcard S3 policy.
