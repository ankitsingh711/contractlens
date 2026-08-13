from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RerankCandidate:
    id: str
    text: str


@dataclass
class RerankResult:
    id: str
    score: float  # normalized to [0, 1], higher is more relevant


class Reranker(ABC):
    """Abstraction over cross-encoder reranking so the retrieval pipeline
    never depends on a specific reranker. Swap via RERANKER_PROVIDER."""

    @abstractmethod
    async def rerank(
        self, query: str, candidates: list[RerankCandidate]
    ) -> list[RerankResult]:
        """Returns one result per candidate, in the same order given."""
        ...
