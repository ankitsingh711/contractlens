import uuid

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


class RetrieveSourceInput(BaseModel):
    chunk_id: str


class RetrieveSourceOutput(BaseModel):
    found: bool
    document_id: str | None = None
    filename: str | None = None
    page: int | None = None
    section: str | None = None
    heading: str | None = None
    text: str | None = None


async def retrieve_source(
    db: AsyncSession, organization_id: uuid.UUID, input: RetrieveSourceInput
) -> RetrieveSourceOutput:
    """Fetches the full chunk + document context behind a citation, e.g.
    when the UI needs to open the document viewer at the cited page."""
    stmt = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.id == uuid.UUID(input.chunk_id),
            Document.organization_id == organization_id,
            Document.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        return RetrieveSourceOutput(found=False)

    chunk, document = row
    return RetrieveSourceOutput(
        found=True,
        document_id=str(document.id),
        filename=document.filename,
        page=chunk.page,
        section=chunk.section,
        heading=chunk.heading,
        text=chunk.text,
    )
