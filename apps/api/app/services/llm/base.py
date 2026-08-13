from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMProvider(ABC):
    """Abstraction over chat completion so the RAG/agent layer never depends
    on a specific model provider. Swap via LLM_PROVIDER env var."""

    model: str

    @abstractmethod
    async def complete(
        self, messages: list[LLMMessage], *, temperature: float = 0.0
    ) -> LLMResponse: ...
