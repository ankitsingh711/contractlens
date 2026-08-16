# ContractLens AI — Terraform (AWS)

Infrastructure-as-code for the target-state cloud architecture described in
[`docs/architecture.md` §12](../../docs/architecture.md#12-cloud-architecture--target-state-phase-8)
and the root [README](../../README.md). This provisions the AWS equivalent
of what `docker-compose.yml` runs locally: Postgres → RDS, Redis →
ElastiCache, local disk storage → S3, plus everything needed to run
`apps/api` and `apps/web` as containers (ECR, ECS Fargate, ALB, CloudFront,
Secrets Manager, IAM, CloudWatch).

**Status: this has not been applied against a real AWS account** — there
are no credentials available in the environment this was written in. It has
been validated with `terraform fmt` and `terraform validate` (see below),
and reviewed carefully for internal consistency, but treat it as a strong,
reviewable starting point, not battle-tested infrastructure.

## Layout

| File | Purpose |
|---|---|
| `versions.tf` | Terraform/provider version pins, AWS provider config, commented-out S3+DynamoDB remote backend |
| `variables.tf` | All input variables (sizing, region, secrets placeholders) with defaults and descriptions |
| `vpc.tf` | VPC, public/app/data subnets across 2 AZs, NAT gateway(s), route tables, per-tier security groups |
| `ecr.tf` | ECR repositories for `api` and `web` images, with lifecycle policies |
| `rds.tf` | RDS PostgreSQL (pgvector-capable engine), subnet group, parameter group |
| `elasticache.tf` | Single-node ElastiCache Redis replication group |
| `s3.tf` | Private, encrypted, versioned S3 bucket for document storage |
| `secrets.tf` | Secrets Manager secrets for `SECRET_KEY`, DB credentials, LLM/reranker/Langfuse provider keys |
| `iam.tf` | ECS task execution role (ECR/CloudWatch/Secrets) and API task role (S3, scoped to one bucket) |
| `ecs.tf` | ECS cluster, `api`/`web` task definitions and services, CloudWatch log groups |
| `alb.tf` | Application Load Balancer, `api`/`web` target groups, path-based routing (`/api/*` → api) |
| `cloudfront.tf` | CloudFront distribution in front of the ALB, with `/api/*` caching disabled |
| `outputs.tf` | ALB DNS, CloudFront domain, ECR URLs, RDS endpoint, Redis endpoint, bucket name |
| `terraform.tfvars.example` | Example variable values — copy to `terraform.tfvars` (git-ignored) and edit |

## Prerequisites

- An AWS account with permission to create VPCs, RDS, ElastiCache, ECS,
  ECR, S3, IAM roles, Secrets Manager secrets, ALB, and CloudFront
  resources.
- Terraform >= 1.6.0 (validated locally with 1.15.7).
- AWS CLI configured with credentials for that account (`aws configure` or
  an assumed role), for both `terraform apply` and the image push step
  below.
- Docker, to build `apps/api` and `apps/web` images for push to ECR.

## Deploy sequence

1. **Bootstrap remote state** (one-time, outside this config — see the
   comment block at the top of `versions.tf`): create an S3 bucket
   (versioned, encrypted) and a DynamoDB table with partition key `LockID`
   for state locking. Uncomment and fill in the `backend "s3"` block in
   `versions.tf`, then `terraform init -migrate-state`.

2. **Configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # edit terraform.tfvars for sizing/region/environment
   export TF_VAR_app_secret_key="$(openssl rand -hex 32)"
   export TF_VAR_openai_api_key="sk-..."   # optional — omit to stay in mock/demo mode
   # ...same pattern for anthropic_api_key / cohere_api_key / langfuse_* if used
   ```

3. **Provision infrastructure**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```
   This creates the VPC/RDS/ElastiCache/S3/ECR/IAM/Secrets/ALB/CloudFront
   resources and an ECS cluster with `api`/`web` services — but the
   services will fail to start healthy yet, because the ECR repos are
   empty (no image pushed with the tag `terraform.tfvars` points at). That
   is expected at this point.

4. **Build and push images** to the ECR repos this apply just created:
   ```bash
   aws ecr get-login-password --region <region> | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

   docker build -t <ecr_api_repository_url>:latest apps/api
   docker push <ecr_api_repository_url>:latest

   docker build -t <ecr_web_repository_url>:latest \
     --build-arg NEXT_PUBLIC_API_URL=https://<cloudfront_domain_name>/api apps/web
   docker push <ecr_web_repository_url>:latest
   ```
   (`terraform output ecr_api_repository_url` / `ecr_web_repository_url` /
   `cloudfront_domain_name` give the real values.)

5. **Run the database migration once the schema doesn't exist yet.** Before
   the API can serve traffic, run `alembic upgrade head` against the RDS
   instance. See the important caveat below about the `vector` extension —
   it must be created *before* migrations run. The simplest path is via
   `aws ecs execute-command` into a running API task (enabled on the
   service — see `ecs.tf`) once step 6 has at least one task up, or via a
   bastion/SSM port-forward session if you'd rather run it from a laptop.

6. **Force a fresh deployment** so the services pick up the pushed images:
   ```bash
   aws ecs update-service --cluster <ecs_cluster_name> --service <ecs_api_service_name> --force-new-deployment
   aws ecs update-service --cluster <ecs_cluster_name> --service <ecs_web_service_name> --force-new-deployment
   ```

7. Visit `terraform output cloudfront_domain_name` (or the ALB DNS name
   directly, for testing without CloudFront's cache in the way).

### pgvector extension — read before running migrations

Verified directly against this repo, not assumed: none of the Alembic
migrations under `apps/api/app/db/migrations/versions/` contain a `CREATE
EXTENSION vector` statement. Locally this is invisible because the
`pgvector/pgvector:pg16` Docker image's `initdb` bootstrap already has the
extension created in the default database. RDS does not do that
automatically — pgvector is *available* on RDS Postgres 15+, but still
needs to be explicitly enabled once per database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Run this once, by hand, against the RDS instance before the first `alembic
upgrade head`. The cleaner long-term fix is a one-line addition to the
earliest Alembic migration (`op.execute("CREATE EXTENSION IF NOT EXISTS
vector")`) so `alembic upgrade head` alone is sufficient on any fresh
Postgres 15+ target — that's an `apps/api` change, intentionally out of
scope for this Terraform-only phase (this PR does not touch `apps/api/`).

## What this does NOT do

- **No CI/CD wiring.** Nothing here auto-applies on merge or auto-builds
  images on push. `docs/architecture.md` sketches a GitHub Actions step
  that would build/push to ECR and run `terraform apply`; that pipeline is
  not implemented in this phase.
- **Not applied against a real AWS account.** Validated with `terraform
  validate`/`fmt` only — there is no `terraform plan`/`apply` output
  against real AWS in this repo's history, and no guarantee every
  attribute is accepted exactly as written until it's tried against a real
  account (e.g. AZ availability for `db.t4g.micro` varies by account/region
  and may need adjusting).
- **No WAF.** CloudFront/ALB have no AWS WAF web ACL attached — worth
  adding before this fronts real user traffic (rate-based rules, managed
  rule groups for common exploits).
- **No multi-region or DR story.** Single region, single RDS instance
  (Multi-AZ is a variable, off by default — see `var.db_multi_az`), no
  cross-region replication, no documented RTO/RPO.
- **No cost estimate included.** Defaults are chosen to be cheap
  (`db.t4g.micro`, `cache.t4g.micro`, one NAT gateway, `PriceClass_100`),
  but no `infracost`-style breakdown is included in this PR.
- **No autoscaling policies on the ECS services.** `desired_count` is
  static (`var.api_desired_count` / `var.web_desired_count`); an
  `aws_appautoscaling_target`/`policy` pair keyed on CPU or ALB request
  count would be the natural next addition.
- **No VPC endpoints.** ECS tasks reach ECR/S3/Secrets Manager over the
  NAT gateway's public route, not PrivateLink endpoints — fine at this
  scale, adds NAT data-transfer cost, and is a first thing to add if this
  needs tightening or cost optimization.
- **Self-hosted Langfuse is not stood up here**, matching the app-level
  scope decision documented in the root README — `LANGFUSE_HOST` points at
  Langfuse Cloud or an externally-run instance, not infrastructure this
  module creates.

## Validation performed

```
$ terraform fmt -check -recursive .
(clean — no output)

$ terraform init -backend=false
Terraform has been successfully initialized!

$ terraform validate
Success! The configuration is valid.
```

`init` was run with `-backend=false` (equivalently: no `backend` block is
active, since it's commented out in `versions.tf`) so it only needs to
download the `aws`/`random` provider plugins — no AWS credentials or real
backend required. `validate` checks HCL syntax, resource/variable
references, and type consistency; it does not (and cannot, without
credentials) confirm every argument is accepted by the AWS API or that IAM
permissions are sufficient — that only a real `plan`/`apply` can prove.
