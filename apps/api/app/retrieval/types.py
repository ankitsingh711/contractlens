import uuid
from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int | None
    section: str | None
    heading: str | None
    chunk_type: str
    text: str
    vector_score: float | None = None
    keyword_score: float | None = None
    fused_score: float | None = None
    rerank_score: float | None = None


@dataclass
class RetrievalResult:
    query: str
    chunks: list[RetrievedChunk]
    evidence_score: float
