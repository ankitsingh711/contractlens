import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentStepResponse(BaseModel):
    id: uuid.UUID
    step_index: int
    step_name: str
    input: dict[str, Any]
    output: dict[str, Any]
    latency_ms: float
    error: str | None

    model_config = {"from_attributes": True}


class AgentRunResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID | None
    query: str
    intent: str | None
    status: str
    answer: str | None
    citations: list[dict[str, Any]]
    evidence_score: float | None
    confidence: float | None
    model: str | None
    prompt_version: str | None
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None
    latency_ms: float | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentRunDetailResponse(AgentRunResponse):
    steps: list[AgentStepResponse]


class AgentRunListResponse(BaseModel):
    agent_runs: list[AgentRunResponse]
