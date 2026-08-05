import pytest

from app.application.analytics.charts import ChartGenerationError, build_chart_from_result
from app.application.analytics.results import QueryResult


def _result() -> QueryResult:
    return QueryResult(
        columns=["period", "refund_rate", "ticket_count"],
        rows=[["before", 0.041, 120], ["after", 0.052, 180]],
        row_count=2,
    )


def test_builds_a_chart_spec_from_a_query_result():
    spec = build_chart_from_result(
        _result(), chart_type="line", title="Refund Rate Over Time", x_column="period", series_columns=["refund_rate"]
    )

    assert spec.type == "line"
    assert spec.title == "Refund Rate Over Time"
    assert spec.x == ["before", "after"]
    assert len(spec.series) == 1
    assert spec.series[0].name == "refund_rate"
    assert spec.series[0].values == [0.041, 0.052]


def test_supports_multiple_series():
    spec = build_chart_from_result(
        _result(), chart_type="bar", title="Refunds vs Tickets", x_column="period",
        series_columns=["refund_rate", "ticket_count"],
    )
    assert [s.name for s in spec.series] == ["refund_rate", "ticket_count"]
    assert spec.series[1].values == [120, 180]


def test_rejects_unknown_x_column():
    with pytest.raises(ChartGenerationError, match="x_column"):
        build_chart_from_result(_result(), chart_type="line", title="t", x_column="nope", series_columns=["refund_rate"])


def test_rejects_unknown_series_column():
    with pytest.raises(ChartGenerationError, match="series_columns"):
        build_chart_from_result(_result(), chart_type="line", title="t", x_column="period", series_columns=["nope"])
