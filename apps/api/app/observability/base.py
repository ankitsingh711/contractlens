from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceStep:
    name: str
    input: dict[str, Any]
    output: dict[str, Any]
    latency_ms: float
    error: str | None = None


@dataclass
class AgentTrace:
    """Everything worth observing about one agent run: enough to answer
    "what happened, how long did it take, what did it cost" without
    opening the database — the same fields the Agent Runs UI shows."""

    trace_id: str
    organization_id: str
    query: str
    intent: str | None
    answer: str | None
    model: str | None
    prompt_version: str | None
    evidence_score: float
    confidence: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    latency_ms: float
    steps: list[TraceStep] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ObservabilityClient(ABC):
    """Abstraction over LLM observability so the rest of the app never
    depends on a specific backend. See docs/evaluation.md for why this is
    optional-by-default rather than a hard dependency."""

    @abstractmethod
    def record_agent_trace(self, trace: AgentTrace) -> None: ...
