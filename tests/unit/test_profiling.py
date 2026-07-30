from datetime import date

from app.domain.dataset import ColumnDefinition
from app.infrastructure.analytics.profiling import compute_profile_statistics


def test_computes_null_rate_and_unique_count():
    columns = [ColumnDefinition(display_name="status", physical_name="col_1", type="string", nullable=True)]
    rows = [{"col_1": "a"}, {"col_1": "a"}, {"col_1": None}, {"col_1": "b"}]

    stats = compute_profile_statistics(rows, columns)

    assert stats["status"]["null_rate"] == 0.25
    assert stats["status"]["unique_count"] == 2


def test_numeric_column_reports_min_max():
    columns = [ColumnDefinition(display_name="amount", physical_name="col_1", type="decimal", nullable=False)]
    rows = [{"col_1": 10.0}, {"col_1": 25.5}, {"col_1": 3.0}]

    stats = compute_profile_statistics(rows, columns)

    assert stats["amount"]["min"] == 3.0
    assert stats["amount"]["max"] == 25.5


def test_date_column_reports_isoformat_min_max():
    columns = [ColumnDefinition(display_name="order_date", physical_name="col_1", type="date", nullable=False)]
    rows = [{"col_1": date(2024, 7, 1)}, {"col_1": date(2024, 6, 1)}]

    stats = compute_profile_statistics(rows, columns)

    assert stats["order_date"]["min"] == "2024-06-01"
    assert stats["order_date"]["max"] == "2024-07-01"


def test_string_column_has_no_min_max():
    columns = [ColumnDefinition(display_name="name", physical_name="col_1", type="string", nullable=False)]
    rows = [{"col_1": "a"}, {"col_1": "b"}]

    stats = compute_profile_statistics(rows, columns)

    assert "min" not in stats["name"]
    assert "max" not in stats["name"]


def test_empty_dataset_has_zero_null_rate():
    columns = [ColumnDefinition(display_name="x", physical_name="col_1", type="string", nullable=True)]
    stats = compute_profile_statistics([], columns)
    assert stats["x"]["null_rate"] == 0.0
    assert stats["x"]["unique_count"] == 0
