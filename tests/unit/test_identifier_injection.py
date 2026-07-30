"""Proves the ADR-017 / SECURITY.md §24 identifier-injection control: CSV
header text (and the dataset's user-facing name) can never become part of a
physical SQL identifier — only Dataset.id and column position can.

BACKLOG.md 3.4 explicitly calls for "tests for malicious/SQL-metacharacter
column headers" — this is that test.
"""
import uuid

import pytest
from sqlalchemy.schema import CreateTable

from app.domain.dataset import ColumnDefinition
from app.infrastructure.analytics.identifiers import generate_physical_column_name, generate_physical_table_name
from app.infrastructure.analytics.table_builder import build_table
from app.infrastructure.parsers.csv_parser import parse_csv

MALICIOUS_HEADERS = [
    '"; DROP TABLE analytics.orders; --',
    "robert'); DROP TABLE students;--",
    "col1\"; SELECT pg_sleep(5); --",
    "amount) VALUES ((SELECT password FROM app.users)); --",
    "name`; DROP TABLE app.users; --",
    "a\nDROP TABLE analytics.orders;",
]


@pytest.mark.parametrize("malicious_header", MALICIOUS_HEADERS)
def test_physical_table_name_never_contains_header_text(malicious_header):
    dataset_id = uuid.uuid4()
    physical_table_name = generate_physical_table_name(dataset_id)

    assert malicious_header not in physical_table_name
    assert physical_table_name == f"ds_{dataset_id.hex}"
    # Only hex characters and the fixed "ds_" prefix — no SQL metacharacters
    # can appear in the generated name regardless of any header content.
    assert all(c in "0123456789abcdefds_" for c in physical_table_name)


@pytest.mark.parametrize("malicious_header", MALICIOUS_HEADERS)
def test_physical_column_name_never_contains_header_text(malicious_header):
    physical_name = generate_physical_column_name(0)
    assert malicious_header not in physical_name
    assert physical_name == "col_1"


def test_malicious_csv_header_is_only_ever_used_as_display_name():
    import csv
    import io

    malicious_header = MALICIOUS_HEADERS[0]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([malicious_header, "amount"])
    writer.writerow(["SwiftShip", "10"])
    csv_bytes = buffer.getvalue().encode("utf-8")

    parsed = parse_csv(csv_bytes)
    assert parsed.headers[0] == malicious_header  # preserved verbatim as *data*

    columns = [
        ColumnDefinition(
            display_name=header,
            physical_name=generate_physical_column_name(index),
            type="string",
            nullable=False,
        )
        for index, header in enumerate(parsed.headers)
    ]

    dataset_id = uuid.uuid4()
    physical_table_name = generate_physical_table_name(dataset_id)
    table = build_table(physical_table_name, columns)

    # The malicious text must be reachable only via display_name (rendered as
    # text/UI content), and must never appear in the compiled DDL that would
    # be sent to Postgres.
    assert columns[0].display_name == malicious_header
    compiled_ddl = str(CreateTable(table))
    assert malicious_header not in compiled_ddl
    for column in table.columns:
        assert column.name in ("col_1", "col_2")


def test_generated_names_depend_only_on_id_and_position_not_on_content():
    dataset_id = uuid.uuid4()
    name_a = generate_physical_table_name(dataset_id)
    name_b = generate_physical_table_name(dataset_id)
    assert name_a == name_b  # deterministic given the same id

    different_id = uuid.uuid4()
    assert generate_physical_table_name(different_id) != name_a
