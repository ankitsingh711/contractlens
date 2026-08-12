from functools import lru_cache

from app.core.config import get_settings
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.mock import MockEmbeddingProvider

__all__ = ["EmbeddingProvider", "get_embedding_provider"]


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.EMBEDDING_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from app.services.embeddings.openai import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
    return MockEmbeddingProvider(dimensions=settings.EMBEDDING_DIMENSIONS)
