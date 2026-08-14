import uuid
from datetime import datetime

from pydantic import BaseModel


class EvaluationResultResponse(BaseModel):
    id: uuid.UUID
    agent_run_id: uuid.UUID | None
    case_id: str
    category: str
    question: str
    expected_answer: str | None
    answer: str | None
    passed: bool
    abstained: bool
    should_abstain: bool
    retrieval_recall: float
    retrieval_precision: float
    citation_accuracy: float
    faithfulness: float
    answer_relevance: float
    hallucinated: bool
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float

    model_config = {"from_attributes": True}


class RegressionResponse(BaseModel):
    metric: str
    baseline: float
    current: float
    delta: float


class EvaluationRunResponse(BaseModel):
    id: uuid.UUID
    dataset_version: str
    status: str
    error_message: str | None
    total_cases: int
    passed_cases: int
    failed_cases: int
    faithfulness: float | None
    citation_accuracy: float | None
    retrieval_recall: float | None
    retrieval_precision: float | None
    hallucination_rate: float | None
    answer_relevance: float | None
    avg_latency_ms: float | None
    avg_input_tokens: float | None
    avg_output_tokens: float | None
    avg_cost_usd: float | None
    baseline_run_id: uuid.UUID | None
    regressions: list[RegressionResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationRunDetailResponse(EvaluationRunResponse):
    results: list[EvaluationResultResponse]


class EvaluationRunListResponse(BaseModel):
    evaluation_runs: list[EvaluationRunResponse]
