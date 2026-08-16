output "alb_dns_name" {
  description = "ALB DNS name — usable directly for testing, bypassing CloudFront."
  value       = aws_lb.main.dns_name
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain — the app's real public entry point."
  value       = aws_cloudfront_distribution.main.domain_name
}

output "ecr_api_repository_url" {
  description = "ECR repo URL to `docker push` the api image to."
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_web_repository_url" {
  description = "ECR repo URL to `docker push` the web image to."
  value       = aws_ecr_repository.web.repository_url
}

output "rds_endpoint" {
  description = "RDS instance endpoint (host:port)."
  value       = aws_db_instance.main.endpoint
}

output "rds_address" {
  description = "RDS instance address (host only, no port)."
  value       = aws_db_instance.main.address
}

output "redis_primary_endpoint" {
  description = "ElastiCache Redis primary endpoint."
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "s3_documents_bucket" {
  description = "S3 bucket name used for document storage (STORAGE_BACKEND=s3, S3_BUCKET)."
  value       = aws_s3_bucket.documents.bucket
}

output "ecs_cluster_name" {
  description = "ECS cluster name — used for `aws ecs update-service --force-new-deployment`."
  value       = aws_ecs_cluster.main.name
}

output "ecs_api_service_name" {
  value = aws_ecs_service.api.name
}

output "ecs_web_service_name" {
  value = aws_ecs_service.web.name
}

output "db_credentials_secret_arn" {
  description = "Secrets Manager ARN holding the DB username/password/DATABASE_URL."
  value       = aws_secretsmanager_secret.db_credentials.arn
}
