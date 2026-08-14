import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.risk_finding import RiskFinding


class RiskAnalysisStatus(str, PyEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskAnalysis(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "risk_analyses"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[RiskAnalysisStatus] = mapped_column(
        Enum(RiskAnalysisStatus, name="risk_analysis_status"),
        nullable=False,
        default=RiskAnalysisStatus.RUNNING,
    )
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    findings: Mapped[list["RiskFinding"]] = relationship(
        back_populates="risk_analysis", cascade="all, delete-orphan"
    )
