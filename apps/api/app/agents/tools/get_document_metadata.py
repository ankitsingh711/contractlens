import uuid

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_service import get_document


class GetDocumentMetadataInput(BaseModel):
    document_id: str


class GetDocumentMetadataOutput(BaseModel):
    found: bool
    filename: str | None = None
    document_type: str | None = None
    status: str | None = None
    page_count: int | None = None


async def get_document_metadata(
    db: AsyncSession, organization_id: uuid.UUID, input: GetDocumentMetadataInput
) -> GetDocumentMetadataOutput:
    """Fetches a document's metadata (filename, type, processing status,
    page count) without pulling any chunk content."""
    try:
        document = await get_document(db, uuid.UUID(input.document_id), organization_id)
    except Exception:
        return GetDocumentMetadataOutput(found=False)

    return GetDocumentMetadataOutput(
        found=True,
        filename=document.filename,
        document_type=document.document_type.value,
        status=document.status.value,
        page_count=document.page_count,
    )
