import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """A retrievable document segment (DATA_MODEL.md §7).

    `embedding` is `None` until the arq embedding job (ADR-026) fills it in;
    retrieval must only ever consider chunks where it is populated.
    """

    id: uuid.UUID
    workspace_id: uuid.UUID
    document_id: uuid.UUID

    chunk_index: int
    content: str

    page_number: int | None
    section_title: str | None

    token_count: int

    embedding: list[float] | None
    embedding_model: str | None
    embedding_version: str | None

    metadata: dict

    created_at: datetime
