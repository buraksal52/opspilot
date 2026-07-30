"""CSV -> analytics.* physical table ingestion (ADR-017, ADR-020).

This is the module BACKLOG.md 3.4 specifically calls out for identifier-
injection testing: the CSV header text (untrusted) only ever becomes
`ColumnDefinition.display_name`, never a physical identifier. Physical table
and column names come exclusively from `infrastructure.analytics.identifiers`.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.dataset import ColumnDefinition, Dataset
from app.infrastructure.analytics.identifiers import generate_physical_column_name, generate_physical_table_name
from app.infrastructure.analytics.profiling import compute_profile_statistics
from app.infrastructure.analytics.table_builder import build_table, create_analytics_table, insert_rows
from app.infrastructure.analytics.type_inference import cast_value, infer_column_types
from app.infrastructure.database.repositories.dataset_repository import DatasetRepository
from app.infrastructure.parsers.csv_parser import parse_csv


class DatasetIngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._datasets = DatasetRepository(session)

    async def ingest(self, *, workspace_id: uuid.UUID, data_source_id: uuid.UUID, name: str, content: bytes) -> Dataset:
        parsed = parse_csv(content)

        dataset_id = uuid.uuid4()
        physical_table_name = generate_physical_table_name(dataset_id)

        inferred_types = infer_column_types(parsed.headers, parsed.rows)
        nullable_by_column = _compute_nullability(parsed.rows)

        columns = [
            ColumnDefinition(
                display_name=header,
                physical_name=generate_physical_column_name(index),
                type=inferred_types[index],
                nullable=nullable_by_column[index],
            )
            for index, header in enumerate(parsed.headers)
        ]

        casted_rows = [
            {col.physical_name: cast_value(raw_row[index], col.type) for index, col in enumerate(columns)}
            for raw_row in parsed.rows
        ]

        table = build_table(physical_table_name, columns)
        connection = await self._session.connection()
        await create_analytics_table(connection, table)
        await insert_rows(connection, table, casted_rows)

        profile_statistics = compute_profile_statistics(casted_rows, columns)

        return await self._datasets.create(
            id=dataset_id,
            workspace_id=workspace_id,
            data_source_id=data_source_id,
            name=name,
            description=None,
            physical_table_name=physical_table_name,
            row_count=len(casted_rows),
            column_count=len(columns),
            schema_definition=columns,
            profile_statistics=profile_statistics,
        )


def _compute_nullability(rows: list[list[str]]) -> list[bool]:
    if not rows:
        return []
    nullable = [False] * len(rows[0])
    for row in rows:
        for index, cell in enumerate(row):
            if cell.strip() == "":
                nullable[index] = True
    return nullable
