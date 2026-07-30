import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class DatasetModel(Base):
    __tablename__ = "datasets"
    __table_args__ = (
        CheckConstraint("status IN ('PROCESSING','READY','FAILED')", name="ck_datasets_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app.workspaces.id"), nullable=False, index=True)
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app.data_sources.id"), nullable=False, index=True, unique=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # ADR-017: generated identifier (e.g. `ds_<uuid hex>`), unique, and the
    # only name ever used to build DDL/DML against the `analytics` schema.
    physical_table_name: Mapped[str] = mapped_column(String(63), nullable=False, unique=True)

    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)

    schema_definition: Mapped[list] = mapped_column(JSONB, nullable=False)
    profile_statistics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
