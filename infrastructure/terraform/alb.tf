# One ALB, path-based routing to two target groups (api, web) — cheaper and
# simpler than standing up two ALBs for a portfolio-scale deployment, and
# the standard pattern for "a handful of services behind one load balancer"
# on ECS. `/api/*` (matching apps/api's API_PREFIX = "/api") routes to the
# FastAPI target group; everything else falls through to the default
# action, which is the Next.js web target group.
#
# Note: CloudFront (cloudfront.tf) sits in front of this ALB and already
# does the same path-based split at the edge with different caching
# behavior per path. The ALB-level rule is kept anyway so the ALB is
# correct and independently testable (e.g. hitting it directly, bypassing
# CloudFront, still routes correctly) rather than relying solely on
# CloudFront's behavior configuration.

resource "aws_lb" "main" {
  name               = "${local.name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "production"

  tags = { Name = "${local.name}-alb" }
}

resource "aws_lb_target_group" "api" {
  name        = "${local.name}-tg-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip" # required for Fargate

  health_check {
    path                = "/api/health"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  deregistration_delay = 30

  tags = { Name = "${local.name}-tg-api" }
}

resource "aws_lb_target_group" "web" {
  name        = "${local.name}-tg-web"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  # apps/web has no dedicated /api/health-style endpoint of its own (it's a
  # Next.js standalone server, see apps/web/Dockerfile); "/" is the login
  # page for unauthenticated requests and returns 200, so it's a reasonable
  # default health check target. Revisit if a dedicated /healthz route is
  # added to the web app.
  health_check {
    path                = "/"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  deregistration_delay = 30

  tags = { Name = "${local.name}-tg-web" }
}

# HTTP listener: redirect to HTTPS if a certificate is configured,
# otherwise (no domain/cert supplied) serve HTTP directly so this still
# stands up and is testable without owning a domain.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = var.acm_certificate_arn != "" ? [1] : []
    content {
      type = "redirect"
      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = var.acm_certificate_arn == "" ? [1] : []
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.web.arn
    }
  }
}

resource "aws_lb_listener" "https" {
  count             = var.acm_certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

locals {
  # Attach the /api/* rule to whichever listener is actually serving
  # traffic: HTTPS if a cert was supplied, otherwise the plain HTTP
  # listener (which in that case forwards directly instead of redirecting).
  primary_listener_arn = var.acm_certificate_arn != "" ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = local.primary_listener_arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
