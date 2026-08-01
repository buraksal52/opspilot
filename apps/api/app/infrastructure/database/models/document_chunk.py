import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base

# Fixed by ADR-025 (Gemini `gemini-embedding-001`, output_dimensionality=768).
# This is a physical column width: changing it requires a new migration, not
# just an updated `Settings.embedding_dimension` default — the two are kept in
# sync by convention (checked by tests/unit/test_document_chunk_model.py),
# not by reading settings at class-definition time.
EMBEDDING_DIMENSION = 768


class DocumentChunkModel(Base):
    """A retrievable document segment (DATA_MODEL.md §7).

    `embedding` is nullable: chunks are created synchronously during ingestion
    (parsing + chunking is pure CPU work), while the vector itself is filled
    in asynchronously by the arq embedding job (ADR-026). Retrieval queries
    must always filter `WHERE embedding IS NOT NULL`.
    """

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app.workspaces.id"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app.documents.id"), nullable=False, index=True)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Approximate size estimate used only for chunk-sizing decisions, not an
    # exact provider token count (ADR-025, RAG_SYSTEM.md §9).
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Dimension fixed by ADR-025's chosen model/output_dimensionality. A future
    # change in dimension requires a new migration + re-embedding, not a
    # silent mix of incompatible vector spaces (RAG_SYSTEM.md §14).
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    chunk_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Postgres-computed (`GENERATED ALWAYS AS ... STORED`, matching the
    # migration's DDL exactly) — `Computed(...)` tells SQLAlchemy this column
    # is server-generated, so it's never included in INSERT/UPDATE statements
    # (a plain nullable column without this would make SQLAlchemy send an
    # explicit NULL, which Postgres rejects for GENERATED ALWAYS columns).
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True), nullable=True
    )
