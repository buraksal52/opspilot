"""add generated tsvector column + GIN index for lexical retrieval

Revision ID: f47b2e6a9c31
Revises: e3a1c9f4b2d7
Create Date: 2026-08-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f47b2e6a9c31'
down_revision: Union[str, Sequence[str], None] = 'e3a1c9f4b2d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ADR-028: PostgreSQL full-text search (tsvector/GIN), no additional
    # infrastructure (RAG_SYSTEM.md §17). GENERATED ALWAYS keeps content_tsv
    # automatically in sync with `content` — the application never writes it.
    op.execute(
        """
        ALTER TABLE app.document_chunks
        ADD COLUMN content_tsv tsvector
        GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
        """
    )
    op.execute(
        "CREATE INDEX ix_app_document_chunks_content_tsv ON app.document_chunks USING GIN (content_tsv)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS app.ix_app_document_chunks_content_tsv")
    op.execute("ALTER TABLE app.document_chunks DROP COLUMN IF EXISTS content_tsv")
