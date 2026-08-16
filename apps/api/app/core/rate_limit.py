import time
from dataclasses import dataclass
from functools import lru_cache

import jwt
import redis.asyncio as redis
from starlette.requests import Request

from app.core.config import get_settings
from app.core.security import decode_access_token

WINDOW_SECONDS = 60


@lru_cache
def get_redis_client() -> redis.Redis:
    """Lazily create a single shared async Redis client for the process.

    Mirrors the lru_cache-based provider pattern used elsewhere (e.g.
    app/services/embeddings/__init__.py's get_embedding_provider) so the
    connection pool is created once and reused across requests instead of
    being rebuilt on every call.
    """
    settings = get_settings()
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: int


async def check_rate_limit(identifier: str, limit: int) -> RateLimitResult:
    """Fixed-window rate limit check backed by Redis INCR + EXPIRE.

    Window key includes the current epoch minute so counters reset
    automatically every 60s without needing a background sweep. Callers
    should catch redis.exceptions.RedisError to decide how to handle Redis
    being unavailable.
    """
    client = get_redis_client()
    window = int(time.time()) // WINDOW_SECONDS
    key = f"ratelimit:{identifier}:{window}"

    count = await client.incr(key)
    if count == 1:
        await client.expire(key, WINDOW_SECONDS)

    if count > limit:
        ttl = await client.ttl(key)
        retry_after = ttl if ttl and ttl > 0 else WINDOW_SECONDS
        return RateLimitResult(allowed=False, retry_after=retry_after)

    return RateLimitResult(allowed=True, retry_after=0)


def resolve_identifier(request: Request) -> str:
    """Identify the caller for rate-limiting: authenticated user id if a
    valid bearer token is present, otherwise client IP (respecting
    X-Forwarded-For since this sits behind an ALB in production).
    """
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except (jwt.PyJWTError, KeyError, ValueError):
            pass

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    else:
        ip = "unknown"
    return f"ip:{ip}"
