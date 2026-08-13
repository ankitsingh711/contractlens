from typing import Any, TypedDict


class AgentState(TypedDict):
    query: str
    organization_id: str
    document_ids: list[str]
    intent: str
    retrieved_chunks: list[dict[str, Any]]
    evidence_score: float
    answer: str | None
    citations: list[dict[str, Any]]
    confidence: float
    tool_calls: list[dict[str, Any]]
    errors: list[str]
