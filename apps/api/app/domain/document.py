import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DocumentType(StrEnum):
    PDF = "PDF"
    MARKDOWN = "MARKDOWN"
    TEXT = "TEXT"


@dataclass(frozen=True, slots=True)
class Document:
    id: uuid.UUID
    workspace_id: uuid.UUID
    data_source_id: uuid.UUID
    title: str
    document_type: DocumentType
    text_content: str
    page_count: int | None
    language: str | None
    metadata: dict
    created_at: datetime
    updated_at: datetime
