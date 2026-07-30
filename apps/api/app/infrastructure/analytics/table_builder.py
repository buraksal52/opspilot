"""Physical analytics-table creation and row insertion (ADR-017, ADR-020).

Uses SQLAlchemy Core (not the ORM) since the table shape is only known at
ingestion time — exactly the case ADR-020 reserves Core for. All identifiers
come from `analytics.identifiers` (never from user input); all values are
bound as parameters, never string-formatted into SQL.
"""
from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, MetaData, String, Table
from sqlalchemy.ext.asyncio import AsyncConnection

from app.domain.dataset import ColumnDefinition

ANALYTICS_SCHEMA = "analytics"

_SQLALCHEMY_TYPES = {
    "integer": Integer(),
    "decimal": Float(),
    "boolean": Boolean(),
    "date": Date(),
    "datetime": DateTime(timezone=True),
    "string": String(),
}


def build_table(physical_table_name: str, columns: list[ColumnDefinition]) -> Table:
    metadata = MetaData(schema=ANALYTICS_SCHEMA)
    sa_columns = [
        Column(col.physical_name, _SQLALCHEMY_TYPES.get(col.type, String()), nullable=col.nullable)
        for col in columns
    ]
    return Table(physical_table_name, metadata, *sa_columns)


async def create_analytics_table(connection: AsyncConnection, table: Table) -> None:
    await connection.run_sync(lambda sync_conn: table.metadata.create_all(sync_conn, tables=[table]))


async def insert_rows(connection: AsyncConnection, table: Table, rows: list[dict]) -> None:
    if not rows:
        return
    await connection.execute(table.insert(), rows)
