import uuid

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk


class GetClauseInput(BaseModel):
    document_id: str
    section: str = Field(min_length=1, max_length=64)


class GetClauseOutput(BaseModel):
    found: bool
    chunk_id: str | None = None
    heading: str | None = None
    page: int | None = None
    text: str | None = None


async def get_clause(
    db: AsyncSession, organization_id: uuid.UUID, input: GetClauseInput
) -> GetClauseOutput:
    """Fetches the clause(s) filed under a specific section number in a
    specific document — for when the caller already knows exactly which
    section they want, rather than needing a similarity search."""
    document_id = uuid.UUID(input.document_id)
    stmt = (
        select(DocumentChunk)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.id == document_id,
            Document.organization_id == organization_id,
            Document.status == DocumentStatus.COMPLETED,
            Document.deleted_at.is_(None),
            DocumentChunk.section == input.section,
        )
        .order_by(DocumentChunk.chunk_index)
    )
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    if not chunks:
        return GetClauseOutput(found=False)

    combined_text = "\n\n".join(c.text for c in chunks)
    return GetClauseOutput(
        found=True,
        chunk_id=str(chunks[0].id),
        heading=chunks[0].heading,
        page=chunks[0].page,
        text=combined_text,
    )
