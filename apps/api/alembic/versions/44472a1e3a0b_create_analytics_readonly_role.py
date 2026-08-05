"""create analytics readonly role

Revision ID: 44472a1e3a0b
Revises: f47b2e6a9c31
Create Date: 2026-08-05 03:04:14.780941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44472a1e3a0b'
down_revision: Union[str, Sequence[str], None] = 'f47b2e6a9c31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ADR-032: a NOLOGIN role the application connection switches into via
# `SET LOCAL ROLE` for analytical query execution (AnalyticsQueryExecutor),
# never a second login credential/secret. Must match Settings.analytics_readonly_role
# (core/config.py) — if that setting is ever changed from its default, this
# migration's literal role name must be updated to match.
ANALYTICS_READONLY_ROLE = "opspilot_analytics_ro"


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"CREATE ROLE {ANALYTICS_READONLY_ROLE} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE")
    # Grants membership to whichever role is running this migration (the
    # application's own connecting user), so `SET LOCAL ROLE` succeeds
    # without needing to know the configured POSTGRES_USER value literally.
    op.execute(f"GRANT {ANALYTICS_READONLY_ROLE} TO CURRENT_USER")
    op.execute(f"GRANT USAGE ON SCHEMA analytics TO {ANALYTICS_READONLY_ROLE}")
    # SECURITY.md §8: SELECT-only, and covers per-Dataset tables created
    # after this migration runs (ADR-017 — analytics tables are created
    # programmatically at ingestion time, not via Alembic).
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO {ANALYTICS_READONLY_ROLE}")
    op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO {ANALYTICS_READONLY_ROLE}")
    # No privileges of any kind are granted on the `app` schema — the role
    # cannot see application tables even with USAGE unset there (SECURITY.md §13).


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics FROM {ANALYTICS_READONLY_ROLE}")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA analytics REVOKE SELECT ON TABLES FROM {ANALYTICS_READONLY_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA analytics FROM {ANALYTICS_READONLY_ROLE}")
    op.execute(f"REVOKE {ANALYTICS_READONLY_ROLE} FROM CURRENT_USER")
    op.execute(f"DROP ROLE {ANALYTICS_READONLY_ROLE}")
