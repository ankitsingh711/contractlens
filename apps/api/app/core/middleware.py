import time
import uuid

from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.errors import RateLimitError
from app.core.logging import get_logger
from app.core.rate_limit import check_rate_limit, resolve_identifier

logger = get_logger("http")

RATE_LIMIT_EXEMPT_PATHS = {"/api/health", "/docs", "/openapi.json"}
# Requests using these methods never mutate state, so they're excluded from
# the rate-limit budget. This app relies on client-side polling (document
# processing status, evaluation run status) which can easily fire dozens of
# GET requests within a minute under completely normal use; the actual abuse
# surface this middleware needs to cover (login/register brute-forcing,
# write spam) is on mutating requests.
RATE_LIMIT_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID and logs structured access records."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["x-request-id"] = request_id
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed fixed-window rate limiter, applied globally.

    Identifies callers by authenticated user id when a valid bearer token
    is present, otherwise by client IP, so both authenticated abuse and
    anonymous brute-forcing (e.g. against /api/auth/login) are covered.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if (
            request.method in RATE_LIMIT_SAFE_METHODS
            or request.url.path in RATE_LIMIT_EXEMPT_PATHS
        ):
            return await call_next(request)

        settings = get_settings()
        identifier = resolve_identifier(request)

        try:
            result = await check_rate_limit(identifier, settings.RATE_LIMIT_PER_MINUTE)
        except RedisError as exc:
            # Fail open: this deployment has no redundancy for Redis yet, so
            # treating an outage as "reject every request" would take down
            # the whole API over a non-security failure. Availability wins
            # over strict enforcement here.
            logger.warning("rate_limit_check_failed", error=str(exc))
            return await call_next(request)

        if not result.allowed:
            request_id = getattr(request.state, "request_id", "unknown")
            error = RateLimitError()
            return JSONResponse(
                status_code=error.status_code,
                content={
                    "error": {
                        "code": error.code,
                        "message": error.message,
                        "request_id": request_id,
                    }
                },
                headers={"Retry-After": str(result.retry_after)},
            )

        return await call_next(request)
