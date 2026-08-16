# S3 bucket for document storage — the production target for
# STORAGE_BACKEND=s3 (apps/api/app/services/storage/s3.py). That backend
# only ever calls put_object/get_object/delete_object/generate_presigned_url
# using the API's own credentials (its ECS task role, in production — see
# iam.tf) and hands out short-lived presigned GET URLs to the frontend. The
# frontend and internet never talk to the bucket directly otherwise, so the
# bucket is private with all public access blocked — there is no code path
# in the app that needs or expects public bucket access.

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "documents" {
  bucket        = "${var.project_name}-documents-${var.environment}-${random_id.bucket_suffix.hex}"
  force_destroy = var.document_bucket_force_destroy

  tags = { Name = "${local.name}-documents" }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    # Contract documents are legal records; versioning protects against
    # accidental overwrite/delete (the app never overwrites a key in place,
    # but this is cheap insurance) at the cost of needing lifecycle rules
    # to expire noncurrent versions eventually.
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {} # applies to every object in the bucket

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_policy" "documents" {
  bucket = aws_s3_bucket.documents.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.documents.arn,
          "${aws_s3_bucket.documents.arn}/*",
        ]
        Condition = {
          Bool = { "aws:SecureTransport" = "false" }
        }
      }
    ]
  })
}
