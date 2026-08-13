import uuid

from app.models.document import Document
from app.models.document_chunk import DocumentChunk

RRF_K = 60


def reciprocal_rank_fusion(
    vector_results: list[tuple[DocumentChunk, Document, float]],
    keyword_results: list[tuple[DocumentChunk, Document, float]],
) -> list[tuple[DocumentChunk, Document, float, float | None, float | None]]:
    """Fuses two independently-ranked result lists using Reciprocal Rank
    Fusion: score(doc) = sum(1 / (k + rank)) over every list it appears in.

    RRF is used instead of blending raw similarity/rank scores because
    vector cosine similarity and ts_rank live on different, incomparable
    scales — RRF only needs each list's *rank order*, not the scores
    themselves, which is what makes it a standard fusion choice for
    combining semantic and lexical search.
    """
    fused: dict[uuid.UUID, float] = {}
    chunk_lookup: dict[uuid.UUID, tuple[DocumentChunk, Document]] = {}
    vector_scores: dict[uuid.UUID, float] = {}
    keyword_scores: dict[uuid.UUID, float] = {}

    for rank, (chunk, doc, score) in enumerate(vector_results, start=1):
        fused[chunk.id] = fused.get(chunk.id, 0.0) + 1 / (RRF_K + rank)
        chunk_lookup[chunk.id] = (chunk, doc)
        vector_scores[chunk.id] = score

    for rank, (chunk, doc, score) in enumerate(keyword_results, start=1):
        fused[chunk.id] = fused.get(chunk.id, 0.0) + 1 / (RRF_K + rank)
        chunk_lookup[chunk.id] = (chunk, doc)
        keyword_scores[chunk.id] = score

    ordered_ids = sorted(fused.keys(), key=lambda cid: fused[cid], reverse=True)
    return [
        (
            chunk_lookup[cid][0],
            chunk_lookup[cid][1],
            fused[cid],
            vector_scores.get(cid),
            keyword_scores.get(cid),
        )
        for cid in ordered_ids
    ]
