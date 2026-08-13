import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.keyword_search import keyword_search
from app.retrieval.types import RetrievalResult, RetrievedChunk
from app.retrieval.vector_search import vector_search
from app.services.embeddings import get_embedding_provider
from app.services.reranking import get_reranker
from app.services.reranking.base import RerankCandidate

settings = get_settings()


async def hybrid_search(
    db: AsyncSession,
    query: str,
    organization_id: uuid.UUID,
    document_ids: list[uuid.UUID] | None = None,
    top_k: int = 5,
    candidate_pool_size: int = 20,
) -> RetrievalResult:
    """Query -> [vector search + keyword search] -> RRF fusion -> rerank ->
    top-K evidence. See docs/rag.md for why each stage exists."""
    embedding_provider = get_embedding_provider()
    [query_embedding] = await embedding_provider.embed([query])

    # Run sequentially: both share one AsyncSession/connection, which can't
    # execute two statements concurrently.
    vector_results = await vector_search(
        db, query_embedding, organization_id, document_ids, candidate_pool_size
    )
    keyword_results = await keyword_search(
        db, query, organization_id, document_ids, candidate_pool_size
    )

    fused = reciprocal_rank_fusion(vector_results, keyword_results)
    if not fused:
        return RetrievalResult(query=query, chunks=[], evidence_score=0.0)

    candidates = fused[:candidate_pool_size]
    reranker = get_reranker()
    rerank_results = await reranker.rerank(
        query,
        [RerankCandidate(id=str(chunk.id), text=chunk.text) for chunk, _doc, _f, _v, _k in candidates],
    )
    rerank_scores = {r.id: r.score for r in rerank_results}

    retrieved = [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_id=doc.id,
            filename=doc.filename,
            page=chunk.page,
            section=chunk.section,
            heading=chunk.heading,
            chunk_type=chunk.chunk_type.value,
            text=chunk.text,
            vector_score=vector_score,
            keyword_score=keyword_score,
            fused_score=fused_score,
            rerank_score=rerank_scores.get(str(chunk.id), 0.0),
        )
        for chunk, doc, fused_score, vector_score, keyword_score in candidates
    ]
    retrieved.sort(key=lambda c: c.rerank_score or 0.0, reverse=True)
    top = retrieved[:top_k]

    evidence_score = top[0].rerank_score or 0.0 if top else 0.0
    return RetrievalResult(query=query, chunks=top, evidence_score=evidence_score)
