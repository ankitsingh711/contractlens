import re

from app.services.reranking.base import RerankCandidate, Reranker, RerankResult

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class MockReranker(Reranker):
    """Deterministic, dependency-free reranker for demo mode.

    Scores each candidate by what fraction of the query's distinct terms
    it contains (a simple lexical-overlap heuristic), not a cross-encoder.
    This is a stand-in that lets the rerank step of the pipeline be
    exercised without an API key; a real reranker (e.g. Cohere) plugs in
    behind the same interface with no changes to the retrieval pipeline.
    """

    async def rerank(
        self, query: str, candidates: list[RerankCandidate]
    ) -> list[RerankResult]:
        query_tokens = set(_TOKEN_RE.findall(query.lower()))
        if not query_tokens:
            return [RerankResult(id=c.id, score=0.0) for c in candidates]

        results = []
        for candidate in candidates:
            candidate_tokens = set(_TOKEN_RE.findall(candidate.text.lower()))
            overlap = len(query_tokens & candidate_tokens)
            score = overlap / len(query_tokens)
            results.append(RerankResult(id=candidate.id, score=min(score, 1.0)))
        return results
