import hashlib
import math
import re

from app.services.embeddings.base import EmbeddingProvider

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic, dependency-free embedding for demo mode.

    Uses a hashed bag-of-words representation (each token hashes to a fixed
    dimension, weighted by term frequency, L2-normalized) rather than random
    vectors. This makes cosine similarity between chunks that share
    vocabulary meaningfully higher than unrelated chunks, so hybrid
    retrieval and reranking are exercisable end-to-end without an API key —
    it is not a substitute for a real semantic embedding model.
    """

    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _TOKEN_RE.findall(text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]
