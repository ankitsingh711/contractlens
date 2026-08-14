import uuid

from pydantic import BaseModel


class CompareRequest(BaseModel):
    document_id_a: uuid.UUID
    document_id_b: uuid.UUID


class ComparisonSideResponse(BaseModel):
    found: bool
    text: str | None
    page: int | None
    section: str | None
    chunk_id: str | None


class ComparisonRowResponse(BaseModel):
    category: str
    label: str
    document_a: ComparisonSideResponse
    document_b: ComparisonSideResponse


class CompareResponse(BaseModel):
    document_id_a: uuid.UUID
    document_id_b: uuid.UUID
    rows: list[ComparisonRowResponse]
