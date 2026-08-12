from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstraction over embedding generation so the retrieval layer never
    depends on a specific provider. Swap via EMBEDDING_PROVIDER env var."""

    dimensions: int

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Returns one embedding vector per input text, same order."""
        ...
