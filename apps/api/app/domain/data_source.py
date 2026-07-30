import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SourceType(StrEnum):
    CSV = "CSV"
    PDF = "PDF"
    MARKDOWN = "MARKDOWN"
    TEXT = "TEXT"


class DataSourceStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    DELETED = "DELETED"


@dataclass(frozen=True, slots=True)
class DataSource:
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    source_type: SourceType
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: DataSourceStatus
    # Opaque key into FileStorage (infrastructure/storage) — not part of
    # DATA_MODEL.md's public field list, but required internally to locate
    # the raw upload for parsing/deletion.
    storage_key: str
    error_message: str | None
    source_metadata: dict
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None
