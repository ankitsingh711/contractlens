import uuid

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval import hybrid_search


class SearchDocumentsInput(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    document_ids: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class EvidenceChunkPayload(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page: int | None
    section: str | None
    heading: str | None
    text: str
    rerank_score: float | None


class SearchDocumentsOutput(BaseModel):
    evidence_score: float
    chunks: list[EvidenceChunkPayload]


async def search_documents(
    db: AsyncSession, organization_id: uuid.UUID, input: SearchDocumentsInput
) -> SearchDocumentsOutput:
    """Hybrid vector + keyword search over the organization's indexed
    documents — the agent's primary evidence-gathering tool."""
    document_ids = [uuid.UUID(d) for d in input.document_ids] if input.document_ids else None
    result = await hybrid_search(
        db, input.query, organization_id, document_ids=document_ids, top_k=input.top_k
    )
    return SearchDocumentsOutput(
        evidence_score=result.evidence_score,
        chunks=[
            EvidenceChunkPayload(
                chunk_id=str(c.chunk_id),
                document_id=str(c.document_id),
                filename=c.filename,
                page=c.page,
                section=c.section,
                heading=c.heading,
                text=c.text,
                rerank_score=c.rerank_score,
            )
            for c in result.chunks
        ],
    )
