"""Shared analytics result/evidence shapes (ANALYTICS_ENGINE.md §14, DATA_MODEL.md §17)."""
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Normalized SQL execution output (ANALYTICS_ENGINE.md §14). Values are
    already JSON-serializable (Decimal/datetime normalized by the executor)."""

    columns: list[str]
    rows: list[list[Any]]
    row_count: int


@dataclass(frozen=True, slots=True)
class AnalyticsEvidence:
    """Query-evidence-shaped analytics output (DATA_MODEL.md §17) — not yet a
    persisted Evidence row (that requires an Investigation, Phase 6/8), same
    status as `RetrievalResult` in the retrieval layer."""

    dataset_ids: list[uuid.UUID]
    sql: str
    result: QueryResult
