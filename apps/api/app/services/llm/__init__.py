from functools import lru_cache

from app.core.config import get_settings
from app.services.llm.base import LLMMessage, LLMProvider, LLMResponse
from app.services.llm.mock import MockLLMProvider

__all__ = ["LLMMessage", "LLMProvider", "LLMResponse", "get_llm_provider"]


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from app.services.llm.openai import OpenAILLMProvider

        return OpenAILLMProvider(api_key=settings.OPENAI_API_KEY, model=settings.LLM_MODEL)
    return MockLLMProvider()
