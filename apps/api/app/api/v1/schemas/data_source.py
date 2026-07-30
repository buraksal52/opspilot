import uuid
from datetime import datetime

from pydantic import BaseModel


class DataSourceResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    source_type: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None
