"""add document_chunks table with pgvector embedding column

Revision ID: e3a1c9f4b2d7
Revises: ad6b9ab586dc
Create Date: 2026-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e3a1c9f4b2d7'
down_revision: Union[str, Sequence[str], None] = 'ad6b9ab586dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Dimension fixed by ADR-025 (Gemini `gemini-embedding-001`,
# output_dimensionality=768) — must match
# app/infrastructure/database/models/document_chunk.py::EMBEDDING_DIMENSION.
EMBEDDING_DIMENSION = 768


def upgrade() -> None:
    """Upgrade schema."""
    # ADR-004 chose pgvector; ADR-026 switched the Postgres image to
    # pgvector/pgvector:pg16 specifically so this extension is available.
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_title', sa.String(length=512), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False),
        # Nullable: populated asynchronously by the arq embedding job (ADR-026).
        sa.Column('embedding', Vector(EMBEDDING_DIMENSION), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('embedding_version', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['app.documents.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['app.workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='app',
    )
    op.create_index(
        op.f('ix_app_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False, schema='app'
    )
    op.create_index(
        op.f('ix_app_document_chunks_workspace_id'), 'document_chunks', ['workspace_id'], unique=False, schema='app'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_app_document_chunks_workspace_id'), table_name='document_chunks', schema='app')
    op.drop_index(op.f('ix_app_document_chunks_document_id'), table_name='document_chunks', schema='app')
    op.drop_table('document_chunks', schema='app')
    op.execute('DROP EXTENSION IF EXISTS vector')
