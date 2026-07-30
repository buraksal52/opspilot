"""Basic dataset profile statistics (DATA_MODEL.md §8)."""
from datetime import date, datetime
from typing import Any

from app.domain.dataset import ColumnDefinition

_NUMERIC_TYPES = {"integer", "decimal"}
_TEMPORAL_TYPES = {"date", "datetime"}


def compute_profile_statistics(rows: list[dict[str, Any]], columns: list[ColumnDefinition]) -> dict[str, Any]:
    total = len(rows)
    stats: dict[str, Any] = {}

    for col in columns:
        values = [row[col.physical_name] for row in rows]
        non_null = [v for v in values if v is not None]

        col_stats: dict[str, Any] = {
            "null_rate": round(1 - (len(non_null) / total), 4) if total else 0.0,
            "unique_count": len(set(non_null)),
        }

        if non_null and col.type in _NUMERIC_TYPES:
            col_stats["min"] = min(non_null)
            col_stats["max"] = max(non_null)
        elif non_null and col.type in _TEMPORAL_TYPES:
            col_stats["min"] = _isoformat(min(non_null))
            col_stats["max"] = _isoformat(max(non_null))

        stats[col.display_name] = col_stats

    return stats


def _isoformat(value: date | datetime) -> str:
    return value.isoformat()
