from functools import lru_cache

from app.core.config import get_settings
from app.observability.base import AgentTrace, ObservabilityClient, TraceStep
from app.observability.structured_log import StructuredLogObservability

__all__ = ["AgentTrace", "ObservabilityClient", "TraceStep", "get_observability_client"]


@lru_cache
def get_observability_client() -> ObservabilityClient:
    settings = get_settings()
    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        from app.observability.langfuse_client import LangfuseObservability

        return LangfuseObservability(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
    return StructuredLogObservability()
