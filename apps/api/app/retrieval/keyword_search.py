import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk


async def keyword_search(
    db: AsyncSession,
    query_text: str,
    organization_id: uuid.UUID,
    document_ids: list[uuid.UUID] | None,
    limit: int,
) -> list[tuple[DocumentChunk, Document, float]]:
    """PostgreSQL full-text search over chunk text (GIN-indexed tsvector),
    catching exact-term matches (defined terms, section numbers, party
    names) that vector similarity can under-retrieve. Returns (chunk,
    document, rank) tuples ordered by relevance."""
    tsquery = func.websearch_to_tsquery("english", query_text)
    rank = func.ts_rank(DocumentChunk.search_vector, tsquery)

    stmt = (
        select(DocumentChunk, Document, rank.label("rank"))
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.organization_id == organization_id,
            Document.status == DocumentStatus.COMPLETED,
            Document.deleted_at.is_(None),
            DocumentChunk.search_vector.op("@@")(tsquery),
        )
        .order_by(rank.desc())
        .limit(limit)
    )
    if document_ids:
        stmt = stmt.where(Document.id.in_(document_ids))

    result = await db.execute(stmt)
    return [(chunk, doc, float(r)) for chunk, doc, r in result.all()]
