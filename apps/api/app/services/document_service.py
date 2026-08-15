import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DocumentProcessingError, ForbiddenError, NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.document_chunk import DocumentChunk
from app.services.audit_service import log_action
from app.services.embeddings import get_embedding_provider
from app.services.parsing.chunker import chunk_pages
from app.services.parsing.extractors import parse_document
from app.services.storage import get_storage_backend

logger = get_logger("document_service")
settings = get_settings()

_CONTENT_TYPE_TO_DOCUMENT_TYPE = {
    "application/pdf": DocumentType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCX,
    "text/plain": DocumentType.TXT,
}

# Magic-byte signatures for the file types we accept. The client-supplied
# Content-Type header is just a claim — a malicious or buggy client can
# set it to anything, so a mismatched signature (e.g. an .exe renamed to
# report.pdf with Content-Type: application/pdf) is rejected here rather
# than trusted at face value.
_PDF_SIGNATURE = b"%PDF-"
_ZIP_SIGNATURE = b"PK\x03\x04"  # DOCX is a zip container (OOXML)


def resolve_document_type(content_type: str) -> DocumentType:
    document_type = _CONTENT_TYPE_TO_DOCUMENT_TYPE.get(content_type)
    if document_type is None:
        raise ValidationAppError(
            f"Unsupported file type '{content_type}'. Allowed types: PDF, DOCX, TXT."
        )
    return document_type


def _validate_file_content(data: bytes, document_type: DocumentType) -> None:
    """Verifies the file's actual bytes match its declared type, instead
    of trusting the client-supplied Content-Type header alone."""
    if document_type == DocumentType.PDF and not data.startswith(_PDF_SIGNATURE):
        raise ValidationAppError(
            "The file's content does not match a PDF — the upload was rejected."
        )
    elif document_type == DocumentType.DOCX and not data.startswith(_ZIP_SIGNATURE):
        raise ValidationAppError(
            "The file's content does not match a DOCX file — the upload was rejected."
        )
    elif document_type == DocumentType.TXT:
        if data.startswith(_PDF_SIGNATURE) or data.startswith(_ZIP_SIGNATURE):
            raise ValidationAppError(
                "The file's content does not match a plain text file — the upload was rejected."
            )
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationAppError("The text file is not valid UTF-8.") from exc


async def create_document(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    owner_id: uuid.UUID,
    filename: str,
    content_type: str,
    data: bytes,
    ip_address: str | None = None,
) -> Document:
    document_type = resolve_document_type(content_type)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise ValidationAppError(
            f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit."
        )
    if len(data) == 0:
        raise ValidationAppError("The uploaded file is empty.")

    _validate_file_content(data, document_type)

    document = Document(
        organization_id=organization_id,
        owner_id=owner_id,
        filename=filename,
        document_type=document_type,
        content_type=content_type,
        size_bytes=len(data),
        storage_key="",
        status=DocumentStatus.UPLOADING,
    )
    db.add(document)
    await db.flush()

    storage_key = f"{organization_id}/{document.id}/{filename}"
    storage = get_storage_backend()
    await storage.put(storage_key, data, content_type)

    document.storage_key = storage_key
    document.status = DocumentStatus.PROCESSING
    await db.commit()
    await db.refresh(document)

    await log_action(
        db,
        organization_id=organization_id,
        user_id=owner_id,
        action="document.upload",
        resource_type="document",
        resource_id=str(document.id),
        metadata={"filename": filename, "size_bytes": len(data)},
        ip_address=ip_address,
    )
    return document


async def process_document(document_id: uuid.UUID) -> None:
    """Runs the parse -> chunk -> embed -> index pipeline for one document.

    Uses its own DB session because it runs as a background task after the
    HTTP request (and its request-scoped session) has already completed.
    """
    async with AsyncSessionLocal() as db:
        document = await db.get(Document, document_id)
        if document is None:
            logger.error("process_document.missing_document", document_id=str(document_id))
            return

        try:
            document.status = DocumentStatus.PARSING
            await db.commit()

            storage = get_storage_backend()
            data = await storage.get(document.storage_key)
            pages = parse_document(data, document.document_type.value)

            document.status = DocumentStatus.CHUNKING
            await db.commit()
            chunks = chunk_pages(pages)
            if not chunks:
                raise DocumentProcessingError("No content could be extracted for indexing.")

            document.status = DocumentStatus.EMBEDDING
            await db.commit()
            provider = get_embedding_provider()
            embeddings = await provider.embed([c.text for c in chunks])

            document.status = DocumentStatus.INDEXING
            await db.commit()
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk.chunk_index,
                        page=chunk.page,
                        section=chunk.section,
                        heading=chunk.heading,
                        chunk_type=chunk.chunk_type,
                        text=chunk.text,
                        token_count=chunk.token_count,
                        embedding=embedding,
                    )
                )

            page_numbers = [p.number for p in pages if p.number is not None]
            document.page_count = max(page_numbers) if page_numbers else len(pages)
            document.status = DocumentStatus.COMPLETED
            await db.commit()
            logger.info(
                "process_document.completed",
                document_id=str(document_id),
                chunk_count=len(chunks),
            )
        except DocumentProcessingError as exc:
            await db.rollback()
            document = await db.get(Document, document_id)
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)
            await db.commit()
            logger.warning(
                "process_document.failed", document_id=str(document_id), reason=str(exc)
            )
        except Exception as exc:
            await db.rollback()
            document = await db.get(Document, document_id)
            document.status = DocumentStatus.FAILED
            document.error_message = "An unexpected error occurred while processing this document."
            await db.commit()
            logger.error(
                "process_document.unexpected_error",
                document_id=str(document_id),
                error=str(exc),
            )


async def list_documents(db: AsyncSession, organization_id: uuid.UUID) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.organization_id == organization_id, Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def get_document(
    db: AsyncSession, document_id: uuid.UUID, organization_id: uuid.UUID
) -> Document:
    document = await db.get(Document, document_id)
    if document is None or document.deleted_at is not None:
        raise NotFoundError("Document not found.")
    if document.organization_id != organization_id:
        raise ForbiddenError("You do not have access to this document.")
    return document


async def delete_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    organization_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
) -> None:
    """Soft-deletes the document so it disappears from listings/retrieval
    while remaining recoverable; the underlying file and chunks are left
    in place rather than purged immediately."""
    document = await get_document(db, document_id, organization_id)
    document.deleted_at = func.now()
    await db.commit()

    await log_action(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="document.delete",
        resource_type="document",
        resource_id=str(document_id),
        metadata={"filename": document.filename},
        ip_address=ip_address,
    )
