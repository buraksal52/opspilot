"""Dataset catalog (ANALYTICS_ENGINE.md §5-7, BACKLOG.md 5.1).

Per ADR-017, this is built dynamically per request, scoped to the requesting
workspace's own READY Dataset records — never a fixed global table list. Only
display names/columns are exposed here; SQL generation (BACKLOG.md 5.3)
resolves them to physical identifiers separately.
"""
import uuid
from dataclasses import dataclass

from app.application.analytics.known_relationships import KNOWN_RELATIONSHIPS, RelationshipHint
from app.domain.dataset import Dataset, DatasetStatus
from app.infrastructure.database.repositories.dataset_repository import DatasetRepository


@dataclass(frozen=True, slots=True)
class ColumnCatalogEntry:
    display_name: str
    physical_name: str
    type: str
    nullable: bool


@dataclass(frozen=True, slots=True)
class DatasetCatalogEntry:
    dataset_id: uuid.UUID
    display_name: str
    physical_table_name: str
    row_count: int
    columns: list[ColumnCatalogEntry]

    def column(self, display_name: str) -> ColumnCatalogEntry | None:
        for col in self.columns:
            if col.display_name.lower() == display_name.lower():
                return col
        return None


@dataclass(frozen=True, slots=True)
class DatasetCatalog:
    entries: list[DatasetCatalogEntry]
    relationships: list[RelationshipHint]

    def get(self, display_name: str) -> DatasetCatalogEntry | None:
        for entry in self.entries:
            if entry.display_name.lower() == display_name.lower():
                return entry
        return None

    def render(self) -> str:
        """Renders the catalog as text for an LLM prompt (ANALYTICS_ENGINE.md
        §5 example) — display names only, never physical identifiers."""
        lines: list[str] = []
        for entry in self.entries:
            column_names = ", ".join(col.display_name for col in entry.columns)
            lines.append(f"{entry.display_name} ({entry.row_count} rows)\n- columns: {column_names}")
        if self.relationships:
            lines.append("relationships:")
            for rel in self.relationships:
                lines.append(f"- {rel.from_dataset}.{rel.from_column} -> {rel.to_dataset}.{rel.to_column}")
        return "\n".join(lines)


def _to_entry(dataset: Dataset) -> DatasetCatalogEntry:
    return DatasetCatalogEntry(
        dataset_id=dataset.id,
        display_name=dataset.name,
        physical_table_name=dataset.physical_table_name,
        row_count=dataset.row_count,
        columns=[
            ColumnCatalogEntry(
                display_name=col.display_name, physical_name=col.physical_name, type=col.type, nullable=col.nullable
            )
            for col in dataset.schema_definition
        ],
    )


class DatasetCatalogService:
    def __init__(self, dataset_repository: DatasetRepository) -> None:
        self._datasets = dataset_repository

    async def get_catalog(self, workspace_id: uuid.UUID) -> DatasetCatalog:
        datasets = await self._datasets.list_by_workspace(workspace_id)

        # list_by_workspace orders by created_at desc; keep only the most
        # recent Dataset per display name if a name was ever re-uploaded
        # (DATA_MODEL.md §5 — re-upload creates a new Dataset, not a new
        # version of an existing one, so duplicate display names are possible).
        seen_names: set[str] = set()
        entries: list[DatasetCatalogEntry] = []
        for dataset in datasets:
            if dataset.status != DatasetStatus.READY:
                continue
            key = dataset.name.lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            entries.append(_to_entry(dataset))

        present_names = {entry.display_name.lower() for entry in entries}
        relationships = [
            rel
            for rel in KNOWN_RELATIONSHIPS
            if rel.from_dataset.lower() in present_names and rel.to_dataset.lower() in present_names
        ]

        return DatasetCatalog(entries=entries, relationships=relationships)
