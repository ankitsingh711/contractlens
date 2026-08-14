import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.risk_analysis import RiskAnalysis


class RiskSeverity(str, PyEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskFinding(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "risk_findings"

    risk_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_analyses.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[RiskSeverity] = mapped_column(Enum(RiskSeverity, name="risk_severity"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)

    risk_analysis: Mapped["RiskAnalysis"] = relationship(back_populates="findings")
