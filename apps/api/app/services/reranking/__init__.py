from functools import lru_cache

from app.core.config import get_settings
from app.services.reranking.base import RerankCandidate, Reranker, RerankResult
from app.services.reranking.mock import MockReranker

__all__ = ["RerankCandidate", "Reranker", "RerankResult", "get_reranker"]


@lru_cache
def get_reranker() -> Reranker:
    settings = get_settings()
    if settings.RERANKER_PROVIDER == "cohere" and settings.COHERE_API_KEY:
        from app.services.reranking.cohere import CohereReranker

        return CohereReranker(api_key=settings.COHERE_API_KEY, model=settings.RERANKER_MODEL)
    return MockReranker()
