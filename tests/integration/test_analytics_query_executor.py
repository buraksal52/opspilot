"""AnalyticsQueryExecutor against a real Postgres role (ADR-032, SECURITY.md
§38 — cross-workspace/mutation rejection must be verified against the real
database, not just asserted by the validator). Several tests intentionally
call the executor directly with SQL the validator would already reject, to
prove the database role itself is a second, independent enforcement layer.
"""
import uuid

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.infrastructure.analytics.query_executor import (
    AnalyticsExecutionError,
    AnalyticsQueryExecutor,
    AnalyticsQueryTimeoutError,
)
from app.infrastructure.analytics.table_builder import build_table, create_analytics_table, insert_rows
from app.infrastructure.database.session import engine
from app.domain.dataset import ColumnDefinition

pytestmark = pytest.mark.usefixtures("_migrated_database")


@pytest.fixture
def executor():
    settings = get_settings()
    return AnalyticsQueryExecutor(
        engine, readonly_role=settings.analytics_readonly_role, max_rows=500, timeout_seconds=5.0
    )


@pytest.fixture
async def seeded_table(db_session):
    physical_table_name = f"ds_{uuid.uuid4().hex}"
    columns = [
        ColumnDefinition(display_name="order_id", physical_name="col_1", type="string", nullable=False),
        ColumnDefinition(display_name="total_amount", physical_name="col_2", type="decimal", nullable=False),
    ]
    table = build_table(physical_table_name, columns)
    connection = await db_session.connection()
    await create_analytics_table(connection, table)
    await insert_rows(connection, table, [{"col_1": "ORD-1", "col_2": 12.5}, {"col_1": "ORD-2", "col_2": 7.25}])
    await db_session.commit()
    return physical_table_name


async def test_executes_a_valid_select_and_normalizes_decimal_values(executor, seeded_table):
    result = await executor.execute(f"SELECT col_1, col_2 FROM analytics.{seeded_table} ORDER BY col_1")

    assert result.columns == ["col_1", "col_2"]
    assert result.rows == [["ORD-1", 12.5], ["ORD-2", 7.25]]
    assert result.row_count == 2
    assert isinstance(result.rows[0][1], float)  # Decimal normalized to float


async def test_readonly_role_rejects_mutation_even_without_the_validator(executor, seeded_table):
    with pytest.raises(AnalyticsExecutionError):
        await executor.execute(f"DELETE FROM analytics.{seeded_table}")


async def test_readonly_role_cannot_read_the_app_schema(executor):
    with pytest.raises(AnalyticsExecutionError):
        await executor.execute("SELECT * FROM app.users")


async def test_mutation_attempt_does_not_actually_delete_rows(executor, seeded_table, db_session):
    with pytest.raises(AnalyticsExecutionError):
        await executor.execute(f"DELETE FROM analytics.{seeded_table}")

    count = await db_session.execute(text(f"SELECT COUNT(*) FROM analytics.{seeded_table}"))
    assert count.scalar() == 2


async def test_query_exceeding_timeout_raises_timeout_error():
    settings = get_settings()
    short_timeout_executor = AnalyticsQueryExecutor(
        engine, readonly_role=settings.analytics_readonly_role, max_rows=500, timeout_seconds=0.2
    )

    with pytest.raises(AnalyticsQueryTimeoutError):
        await short_timeout_executor.execute("SELECT pg_sleep(2)")


async def test_result_is_capped_at_max_rows_even_without_an_explicit_limit(seeded_table):
    settings = get_settings()
    capped_executor = AnalyticsQueryExecutor(
        engine, readonly_role=settings.analytics_readonly_role, max_rows=1, timeout_seconds=5.0
    )

    result = await capped_executor.execute(f"SELECT col_1 FROM analytics.{seeded_table}")
    assert result.row_count == 1
