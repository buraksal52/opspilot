import pytest

from app.infrastructure.parsers.base import ParserError
from app.infrastructure.parsers.csv_parser import parse_csv


def _csv(text: str) -> bytes:
    return text.encode("utf-8")


def test_parses_well_formed_csv():
    result = parse_csv(_csv("order_id,amount\nORD-1,10.5\nORD-2,20\n"))
    assert result.headers == ["order_id", "amount"]
    assert result.rows == [["ORD-1", "10.5"], ["ORD-2", "20"]]


def test_rejects_empty_file():
    with pytest.raises(ParserError, match="empty"):
        parse_csv(_csv(""))


def test_rejects_header_only_csv():
    with pytest.raises(ParserError, match="no data rows"):
        parse_csv(_csv("order_id,amount\n"))


def test_rejects_ragged_rows():
    with pytest.raises(ParserError, match="column"):
        parse_csv(_csv("a,b,c\n1,2\n"))


def test_rejects_duplicate_headers_case_insensitive():
    with pytest.raises(ParserError, match="duplicate"):
        parse_csv(_csv("order_id,Order_Id\n1,2\n"))


def test_rejects_oversized_cell():
    huge_cell = "x" * 10_001
    with pytest.raises(ParserError, match="exceeding"):
        parse_csv(_csv(f"a\n{huge_cell}\n"))


def test_rejects_too_many_columns():
    headers = ",".join(f"col{i}" for i in range(201))
    row = ",".join("1" for _ in range(201))
    with pytest.raises(ParserError, match="maximum supported column count"):
        parse_csv(_csv(f"{headers}\n{row}\n"))


def test_rejects_invalid_utf8():
    with pytest.raises(ParserError, match="UTF-8"):
        parse_csv(b"a,b\n\xff\xfe,2\n")


def test_tolerates_utf8_bom():
    bom = b"\xef\xbb\xbf"
    result = parse_csv(bom + _csv("a,b\n1,2\n"))
    assert result.headers == ["a", "b"]
