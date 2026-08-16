# CloudFront in front of the ALB — a single distribution edge-terminates
# TLS/caches the Next.js app's static assets close to users, while
# `/api/*` is configured to bypass caching entirely: those routes are
# dynamic and frequently authenticated (Authorization: Bearer JWT), and
# caching an authenticated response at the edge would leak one user's data
# to another. SSE (`POST /api/chat`) also cannot be cached or buffered by a
# CDN in the way CloudFront's default behavior works, which is another
# reason /api/* is routed with caching disabled and all headers/cookies
# forwarded through untouched.
#
# The origin is the ALB (not S3) for both paths — apps/web needs SSR
# (authenticated dynamic pages per docs/architecture.md), so it cannot be a
# static S3+CloudFront origin; it runs as its own ECS Fargate service
# behind the same ALB as the API (see alb.tf's path-based routing), and
# CloudFront simply fronts that ALB for edge caching/TLS termination.

resource "aws_cloudfront_cache_policy" "api_no_cache" {
  name        = "${local.name}-api-no-cache"
  comment     = "Disable caching for dynamic/authenticated API routes"
  default_ttl = 0
  max_ttl     = 0
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "all"
    }
    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["Authorization", "Accept", "Content-Type", "Origin"]
      }
    }
    query_strings_config {
      query_string_behavior = "all"
    }
  }
}

resource "aws_cloudfront_origin_request_policy" "api_passthrough" {
  name    = "${local.name}-api-passthrough"
  comment = "Forward everything to the ALB for API routes"

  cookies_config {
    cookie_behavior = "all"
  }
  headers_config {
    header_behavior = "allViewer"
  }
  query_strings_config {
    query_string_behavior = "all"
  }
}

resource "aws_cloudfront_distribution" "main" {
  enabled     = true
  comment     = "${local.name} CDN"
  price_class = "PriceClass_100" # US/Canada/Europe edge locations only — cheapest tier, adequate for a portfolio demo

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = var.acm_certificate_arn != "" ? "https-only" : "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default behavior: the web app (Next.js pages/assets). Caching enabled
  # with a short default TTL — this is SSR content, not static export, so
  # we don't cache aggressively by default; Next.js sets its own
  # Cache-Control headers for anything that's actually static (e.g.
  # /_next/static/*), which CloudFront respects via the managed
  # CachingOptimized policy.
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "alb"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6" # AWS managed "CachingOptimized"
  }

  # /api/* — no caching, forward everything (auth headers, cookies, query
  # strings) straight through to the ALB.
  ordered_cache_behavior {
    path_pattern             = "/api/*"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    target_origin_id         = "alb"
    viewer_protocol_policy   = "redirect-to-https"
    compress                 = false # do not buffer/compress SSE (/api/chat) responses
    cache_policy_id          = aws_cloudfront_cache_policy.api_no_cache.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api_passthrough.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = var.acm_certificate_arn == ""
    acm_certificate_arn            = var.acm_certificate_arn != "" ? var.acm_certificate_arn : null
    ssl_support_method             = var.acm_certificate_arn != "" ? "sni-only" : null
    minimum_protocol_version       = var.acm_certificate_arn != "" ? "TLSv1.2_2021" : null
  }

  aliases = var.domain_name != "" ? [var.domain_name] : []

  tags = { Name = "${local.name}-cdn" }
}
