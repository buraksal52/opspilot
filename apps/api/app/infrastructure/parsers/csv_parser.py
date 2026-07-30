"""CSV parsing (SECURITY.md §24, DATA_MODEL.md §9).

Only produces raw string rows plus header text — never touches identifier
generation. Header text and cell content are both untrusted (SECURITY.md
§24) and are only ever used as *display* data downstream; see
infrastructure/analytics/identifiers.py for the actual physical-identifier
generation this file deliberately has nothing to do with.
"""
import csv
import io
from dataclasses import dataclass

from app.infrastructure.parsers.base import ParserError

MAX_CSV_ROWS = 200_000
MAX_CSV_COLUMNS = 200
MAX_CELL_LENGTH = 10_000


@dataclass(frozen=True, slots=True)
class ParsedCsv:
    headers: list[str]
    rows: list[list[str]]


def parse_csv(content: bytes) -> ParsedCsv:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ParserError(f"CSV file is not valid UTF-8: {exc}") from exc

    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        raise ParserError(f"Malformed CSV: {exc}") from exc

    if not rows:
        raise ParserError("CSV file is empty")

    headers = rows[0]
    data_rows = rows[1:]

    if not headers or all(not h.strip() for h in headers):
        raise ParserError("CSV file has no header row")
    if len(headers) > MAX_CSV_COLUMNS:
        raise ParserError(f"CSV exceeds the maximum supported column count ({MAX_CSV_COLUMNS})")

    normalized_headers = [h.strip().lower() for h in headers]
    if len(set(normalized_headers)) != len(normalized_headers):
        raise ParserError("CSV header row contains duplicate column names")

    if not data_rows:
        raise ParserError("CSV file has a header row but no data rows")
    if len(data_rows) > MAX_CSV_ROWS:
        raise ParserError(f"CSV exceeds the maximum supported row count ({MAX_CSV_ROWS})")

    expected_columns = len(headers)
    for row_index, row in enumerate(data_rows):
        if len(row) != expected_columns:
            raise ParserError(f"Row {row_index + 2} has {len(row)} column(s), expected {expected_columns}")
        for cell in row:
            if len(cell) > MAX_CELL_LENGTH:
                raise ParserError(f"Row {row_index + 2} contains a cell exceeding {MAX_CELL_LENGTH} characters")

    return ParsedCsv(headers=headers, rows=data_rows)
