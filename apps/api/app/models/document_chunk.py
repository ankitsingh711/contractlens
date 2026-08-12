import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.document import Document

EMBEDDING_DIMENSIONS = get_settings().EMBEDDING_DIMENSIONS


class ChunkType(str, PyEnum):
    CONTRACT_CLAUSE = "contract_clause"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    OTHER = "other"


class DocumentChunk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    heading: Mapped[str | None] = mapped_column(String(512), nullable=True)
    chunk_type: Mapped[ChunkType] = mapped_column(
        Enum(ChunkType, name="chunk_type"), nullable=False, default=ChunkType.PARAGRAPH
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=True
    )
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', text)", persisted=True)
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_document_id", "document_id"),
        Index("ix_document_chunks_search_vector", "search_vector", postgresql_using="gin"),
        Index(
            "ix_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
