import uuid

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    document_ids: list[uuid.UUID] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class EvidenceChunkResponse(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int | None
    section: str | None
    heading: str | None
    chunk_type: str
    text: str
    vector_score: float | None
    keyword_score: float | None
    fused_score: float | None
    rerank_score: float | None


class SearchResponse(BaseModel):
    query: str
    evidence_score: float
    chunks: list[EvidenceChunkResponse]
