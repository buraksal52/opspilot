"""Read-only analytics SQL execution (SECURITY.md §8/§12, ADR-008, ADR-032).

Runs already-validated SQL on a **dedicated** connection (never the ambient
per-request `AsyncSession`, see ADR-032's Rationale for why), switched into a
restricted, privilege-limited Postgres role for the duration of one
always-rolled-back transaction.
"""
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.application.analytics.results import QueryResult

_VALID_ROLE_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
# Postgres SQLSTATE for query_canceled (statement_timeout firing). Checked via
# sqlstate rather than `isinstance(exc.orig, asyncpg.exceptions.QueryCanceledError)`
# because SQLAlchemy's asyncpg dialect re-wraps the driver exception in its own
# DBAPI shim class; the original asyncpg exception type is only reachable via
# `__cause__`, while `sqlstate` is copied onto the wrapper directly.
_QUERY_CANCELED_SQLSTATE = "57014"


class AnalyticsExecutionError(Exception):
    """Raised when the validated query fails to execute (ARCHITECTURE.md
    §21 — classified, never silently swallowed)."""


class AnalyticsQueryTimeoutError(AnalyticsExecutionError):
    """Raised when the query exceeded the configured statement timeout."""


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class AnalyticsQueryExecutor:
    def __init__(self, engine: AsyncEngine, *, readonly_role: str, max_rows: int, timeout_seconds: float) -> None:
        if not _VALID_ROLE_NAME.match(readonly_role):
            raise ValueError(f"Invalid analytics readonly role name: {readonly_role!r}")
        self._engine = engine
        self._role = readonly_role
        self._max_rows = max_rows
        self._timeout_ms = max(1, int(timeout_seconds * 1000))

    async def execute(self, sql: str) -> QueryResult:
        """`sql` must already be validated (`sql_validator.validate_and_bound`)
        — this method adds no further safety check of its own beyond the
        role's database-enforced privileges (defense in depth, not the
        primary control)."""
        async with self._engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text(f"SET LOCAL ROLE {self._role}"))
                await connection.execute(text(f"SET LOCAL statement_timeout = '{self._timeout_ms}ms'"))
                result = await connection.execute(text(sql))
                columns = list(result.keys())
                rows = [[_normalize_value(v) for v in row] for row in result.fetchmany(self._max_rows)]
            except SQLAlchemyError as exc:
                orig = getattr(exc, "orig", None)
                if getattr(orig, "sqlstate", None) == _QUERY_CANCELED_SQLSTATE:
                    raise AnalyticsQueryTimeoutError(
                        f"Query exceeded the {self._timeout_ms}ms execution timeout."
                    ) from exc
                raise AnalyticsExecutionError(f"Query execution failed: {exc}") from exc
            finally:
                # Read-only by construction — always rolled back, both to
                # avoid depending on statement outcome and to guarantee the
                # role/timeout set via SET LOCAL never outlives this
                # transaction on a connection returned to the pool.
                await transaction.rollback()

        return QueryResult(columns=columns, rows=rows, row_count=len(rows))
