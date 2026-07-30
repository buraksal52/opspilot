"""Physical identifier generation for Dataset ingestion (ADR-017, SECURITY.md §24).

These functions are the entire security boundary against SQL-identifier
injection at ingestion time: they are pure functions of a Dataset's UUID and
a column's position, and never take the CSV header text or filename as
input. A header like `"; DROP TABLE analytics.foo; --"` can only ever end up
as `ColumnDefinition.display_name` (rendered as text, never interpolated
into SQL) — it has no path into a physical identifier.
"""
import uuid

# Postgres identifiers are limited to 63 bytes; "ds_" + 32 hex chars = 35,
# comfortably under that with room to spare.
PHYSICAL_TABLE_PREFIX = "ds_"
PHYSICAL_COLUMN_PREFIX = "col_"


def generate_physical_table_name(dataset_id: uuid.UUID) -> str:
    return f"{PHYSICAL_TABLE_PREFIX}{dataset_id.hex}"


def generate_physical_column_name(column_index: int) -> str:
    """`column_index` is 0-based; generated names are 1-based (col_1, col_2, ...)."""
    return f"{PHYSICAL_COLUMN_PREFIX}{column_index + 1}"
