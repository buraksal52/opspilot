import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class User:
    id: uuid.UUID
    email: str
    hashed_password: str
    display_name: str | None
    created_at: datetime
    updated_at: datetime
