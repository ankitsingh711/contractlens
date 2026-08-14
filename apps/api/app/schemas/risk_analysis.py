import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RiskFindingResponse(BaseModel):
    id: uuid.UUID
    category: str
    severity: str
    title: str
    reason: str
    confidence: float
    citations: list[dict[str, Any]]

    model_config = {"from_attributes": True}


class RiskAnalysisResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    risk_score: int | None
    error_message: str | None
    created_at: datetime
    findings: list[RiskFindingResponse]

    model_config = {"from_attributes": True}
