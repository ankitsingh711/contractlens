# Terraform + provider version pins, and remote state backend.
#
# This is a portfolio/demonstration deployment: the backend block below is
# commented out on purpose. There is no real S3 bucket or DynamoDB lock
# table provisioned for this project. Before running this against a real
# AWS account:
#
#   1. Create an S3 bucket for state (versioning + encryption enabled) and
#      a DynamoDB table with a partition key `LockID` (String) for locking.
#      These two resources should NOT be managed by this same Terraform
#      config (chicken-and-egg problem — bootstrap them by hand or with a
#      tiny separate root module).
#   2. Uncomment the backend block and fill in the real bucket/table/region.
#   3. Run `terraform init -migrate-state` to move from local state.
#
# Until then, `terraform init` uses the default local backend
# (terraform.tfstate in this directory) — fine for `plan`/`validate`
# dry-runs, not safe for team use or real deployments.

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # backend "s3" {
  #   bucket         = "contractlens-terraform-state"       # placeholder — replace
  #   key            = "contractlens/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "contractlens-terraform-locks"        # placeholder — replace
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
