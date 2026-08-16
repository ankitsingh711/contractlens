# ElastiCache Redis — replaces the local redis:7-alpine container.
#
# Sizing/topology justification: today (Phase 7) this app's only real Redis
# usage is `app/core/rate_limit.py` — small fixed-window INCR/EXPIRE
# counters keyed per user/IP, reset every 60s. The README's trade-offs
# section also earmarks Redis as the future backing store for a real task
# queue (replacing in-process BackgroundTasks) once that lands. Neither
# workload is memory- or throughput-heavy, so a single small node
# (cache.t4g.micro, no cluster mode, no read replicas) is the right-sized
# choice for this project's actual scale — provisioning a multi-node
# replication group here would be over-engineering for a rate-limiter.
# replication_group (rather than a bare aws_elasticache_cluster) is still
# used because it's the modern resource, supports easy vertical resize, and
# leaves a clean path to add a replica later (just bump
# num_cache_clusters) without changing the resource type.

resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name}-redis-subnets"
  subnet_ids = aws_subnet.data[*].id
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${local.name}-redis"
  description          = "ContractLens rate-limit counters + future task queue"

  engine         = "redis"
  engine_version = var.redis_engine_version
  node_type      = var.redis_node_type
  port           = 6379

  num_cache_clusters = 1 # single node — see sizing note above

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  automatic_failover_enabled = false # requires >= 2 nodes; not needed at this scale
  snapshot_retention_limit   = 1
  snapshot_window            = "05:00-06:00"
  maintenance_window         = "mon:06:30-mon:07:30"

  tags = { Name = "${local.name}-redis" }
}
