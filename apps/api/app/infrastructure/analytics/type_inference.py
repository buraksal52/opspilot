"""Column type inference and value casting for CSV ingestion (DATA_MODEL.md §8)."""
from datetime import date, datetime

SAMPLE_SIZE = 200

_TYPES_IN_PRIORITY_ORDER = ["boolean", "integer", "decimal", "date", "datetime"]


def infer_column_types(headers: list[str], rows: list[list[str]]) -> list[str]:
    types = []
    for col_index in range(len(headers)):
        sample = [row[col_index].strip() for row in rows[:SAMPLE_SIZE] if row[col_index].strip() != ""]
        types.append(_infer_type(sample))
    return types


def _infer_type(sample: list[str]) -> str:
    if not sample:
        return "string"
    for type_name in _TYPES_IN_PRIORITY_ORDER:
        if all(_matches(type_name, value) for value in sample):
            return type_name
    return "string"


def _matches(type_name: str, value: str) -> bool:
    try:
        cast_value(value, type_name)
        return True
    except ValueError:
        return False


def cast_value(raw: str, type_name: str):
    raw = raw.strip()
    if raw == "":
        return None
    if type_name == "boolean":
        lowered = raw.lower()
        if lowered not in ("true", "false"):
            raise ValueError(f"{raw!r} is not a boolean")
        return lowered == "true"
    if type_name == "integer":
        # int() would also accept "3.0"-style strings via float coercion
        # elsewhere, so require a strict integer literal here.
        body = raw[1:] if raw[0] in "+-" else raw
        if not body.isdigit():
            raise ValueError(f"{raw!r} is not an integer")
        return int(raw)
    if type_name == "decimal":
        return float(raw)
    if type_name == "date":
        # Strict YYYY-MM-DD only — a full timestamp like
        # "2024-07-03T11:11:21+00:00" must fail here so the column is typed
        # "datetime" instead (checked after "date" fails during inference).
        return date.fromisoformat(raw)
    if type_name == "datetime":
        return datetime.fromisoformat(raw)
    return raw
