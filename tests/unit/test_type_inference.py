import pytest

from app.infrastructure.analytics.type_inference import cast_value, infer_column_types


def _types_for(headers, columns):
    rows = [list(row) for row in zip(*columns)]
    return infer_column_types(headers, rows)


def test_infers_integer_column():
    types = _types_for(["n"], [["1", "2", "-3", "004"]])
    assert types == ["integer"]


def test_infers_decimal_column():
    types = _types_for(["amount"], [["1.5", "2", "-3.25"]])
    assert types == ["decimal"]


def test_infers_boolean_column():
    types = _types_for(["active"], [["true", "False", "TRUE"]])
    assert types == ["boolean"]


def test_infers_date_column():
    types = _types_for(["d"], [["2024-06-01", "2024-07-11"]])
    assert types == ["date"]


def test_infers_datetime_column_not_date():
    types = _types_for(["ts"], [["2024-07-03T11:11:21+00:00", "2024-07-04T00:00:00+00:00"]])
    assert types == ["datetime"]


def test_mixed_column_falls_back_to_string():
    types = _types_for(["mixed"], [["1", "abc", "3"]])
    assert types == ["string"]


def test_all_empty_column_defaults_to_string():
    types = _types_for(["blank"], [["", "", ""]])
    assert types == ["string"]


def test_empty_values_are_ignored_for_inference():
    types = _types_for(["n"], [["1", "", "3"]])
    assert types == ["integer"]


@pytest.mark.parametrize(
    "type_name,raw,expected",
    [
        ("integer", "42", 42),
        ("integer", "-7", -7),
        ("decimal", "3.14", 3.14),
        ("boolean", "true", True),
        ("boolean", "False", False),
        ("date", "2024-07-11", None),  # checked via isoformat below
        ("string", "hello", "hello"),
    ],
)
def test_cast_value(type_name, raw, expected):
    result = cast_value(raw, type_name)
    if type_name == "date":
        assert result.isoformat() == "2024-07-11"
    else:
        assert result == expected


def test_cast_value_empty_string_is_none_for_any_type():
    assert cast_value("", "integer") is None
    assert cast_value("  ", "string") is None


def test_cast_value_rejects_non_matching_type():
    with pytest.raises(ValueError):
        cast_value("not-a-number", "integer")
