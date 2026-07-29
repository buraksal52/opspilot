from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Application-domain ORM models (User, Workspace, ...) live in the `app` schema.
# Per-Dataset analytics tables live in `analytics`, created programmatically at
# ingestion time (ADR-017) — they are never Alembic-managed and never share
# this metadata object.
APP_SCHEMA = "app"


class Base(DeclarativeBase):
    metadata = MetaData(schema=APP_SCHEMA)
