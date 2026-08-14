import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.evaluation_result import EvaluationResult


class EvaluationRunStatus(str, PyEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_runs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    dataset_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[EvaluationRunStatus] = mapped_column(
        Enum(EvaluationRunStatus, name="evaluation_run_status"),
        nullable=False,
        default=EvaluationRunStatus.RUNNING,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    faithfulness: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    answer_relevance: Mapped[float | None] = mapped_column(Float, nullable=True)

    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_input_tokens: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_output_tokens: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    baseline_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id"), nullable=True
    )
    regressions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)

    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="evaluation_run", cascade="all, delete-orphan"
    )
