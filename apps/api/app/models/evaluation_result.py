import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.evaluation_run import EvaluationRun


class EvaluationResult(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_results"

    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False
    )
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=True
    )

    case_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    abstained: Mapped[bool] = mapped_column(Boolean, nullable=False)
    should_abstain: Mapped[bool] = mapped_column(Boolean, nullable=False)

    retrieval_recall: Mapped[float] = mapped_column(Float, nullable=False)
    retrieval_precision: Mapped[float] = mapped_column(Float, nullable=False)
    citation_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    faithfulness: Mapped[float] = mapped_column(Float, nullable=False)
    answer_relevance: Mapped[float] = mapped_column(Float, nullable=False)
    hallucinated: Mapped[bool] = mapped_column(Boolean, nullable=False)

    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    evaluation_run: Mapped["EvaluationRun"] = relationship(back_populates="results")
