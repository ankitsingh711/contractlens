import httpx

from app.services.reranking.base import RerankCandidate, Reranker, RerankResult

COHERE_RERANK_URL = "https://api.cohere.com/v2/rerank"


class CohereReranker(Reranker):
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    async def rerank(
        self, query: str, candidates: list[RerankCandidate]
    ) -> list[RerankResult]:
        if not candidates:
            return []

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                COHERE_RERANK_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "query": query,
                    "documents": [c.text for c in candidates],
                },
            )
            response.raise_for_status()
            body = response.json()

        scores_by_index = {r["index"]: r["relevance_score"] for r in body["results"]}
        return [
            RerankResult(id=candidates[i].id, score=scores_by_index.get(i, 0.0))
            for i in range(len(candidates))
        ]
