"""create app and analytics schemas

Revision ID: 7d8471eddb48
Revises: 
Create Date: 2026-07-29 15:32:21.862361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d8471eddb48'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS app")
    # analytics holds per-Dataset physical tables created programmatically at
    # ingestion time (ADR-017) — never Alembic-managed, but the schema itself
    # must exist upfront.
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP SCHEMA IF EXISTS app CASCADE")
    op.execute("DROP SCHEMA IF EXISTS analytics CASCADE")
