import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk


async def vector_search(
    db: AsyncSession,
    query_embedding: list[float],
    organization_id: uuid.UUID,
    document_ids: list[uuid.UUID] | None,
    limit: int,
) -> list[tuple[DocumentChunk, Document, float]]:
    """Approximate nearest-neighbor search over chunk embeddings (pgvector
    cosine distance via the HNSW index). Returns (chunk, document,
    similarity) tuples, similarity in [0, 1] where 1 is identical."""
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(DocumentChunk, Document, distance.label("distance"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.organization_id == organization_id,
            Document.status == DocumentStatus.COMPLETED,
            Document.deleted_at.is_(None),
        )
        # Secondary sort by chunk id: without a deterministic tiebreaker,
        # rows with equal distance have unspecified relative order in
        # Postgres (it can vary run to run with LIMIT), which would make
        # which chunks land in the candidate pool non-deterministic.
        .order_by(distance, DocumentChunk.id)
        .limit(limit)
    )
    if document_ids:
        stmt = stmt.where(Document.id.in_(document_ids))

    result = await db.execute(stmt)
    return [(chunk, doc, 1 - dist) for chunk, doc, dist in result.all()]
