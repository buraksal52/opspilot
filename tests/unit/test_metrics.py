import pytest

from app.application.analytics.metrics import (
    MetricCalculationError,
    calculate_average_delivery_time,
    calculate_metric,
    calculate_percentage_change,
    calculate_refund_rate,
    calculate_revenue_impact,
)


def test_percentage_change_matches_documented_example():
    # ANALYTICS_ENGINE.md §17: 4% -> 5% is +1 percentage point, +25% relative.
    result = calculate_percentage_change(0.04, 0.05, as_rate=True)
    assert result.percentage_point_change == pytest.approx(1.0)
    assert result.relative_change_percent == pytest.approx(25.0)
    assert result.absolute_change == pytest.approx(0.01)


def test_percentage_change_without_as_rate_has_no_percentage_point_value():
    result = calculate_percentage_change(100.0, 150.0)
    assert result.relative_change_percent == pytest.approx(50.0)
    assert result.percentage_point_change is None


def test_percentage_change_handles_zero_before_without_dividing_by_zero():
    result = calculate_percentage_change(0.0, 10.0)
    assert result.relative_change_percent is None
    assert result.absolute_change == 10.0


def test_refund_rate_matches_known_value():
    assert calculate_refund_rate(49, 1000) == pytest.approx(0.049)


def test_refund_rate_rejects_zero_total_orders():
    with pytest.raises(MetricCalculationError):
        calculate_refund_rate(1, 0)


def test_average_delivery_time_matches_known_value():
    assert calculate_average_delivery_time([2.0, 3.0, 4.0]) == pytest.approx(3.0)


def test_average_delivery_time_rejects_empty_input():
    with pytest.raises(MetricCalculationError):
        calculate_average_delivery_time([])


def test_revenue_impact_separates_exact_from_estimated():
    result = calculate_revenue_impact(61074.48, estimated_repeat_purchase_risk=5000.0)
    assert result.directly_refunded_revenue == 61074.48
    assert result.estimated_repeat_purchase_risk == 5000.0
    assert result.total_estimated_impact == pytest.approx(66074.48)
    assert "observed" in result.methodology
    assert "estimate" in result.methodology


def test_revenue_impact_without_estimate_component():
    result = calculate_revenue_impact(61074.48)
    assert result.estimated_repeat_purchase_risk is None
    assert result.total_estimated_impact == 61074.48


def test_revenue_impact_rejects_negative_refunded_revenue():
    with pytest.raises(MetricCalculationError):
        calculate_revenue_impact(-1.0)


def test_calculate_metric_dispatches_by_type():
    assert calculate_metric("refund_rate", refund_count=49, total_order_count=1000) == pytest.approx(0.049)


def test_calculate_metric_rejects_unknown_type():
    with pytest.raises(MetricCalculationError, match="Unknown metric_type"):
        calculate_metric("not_a_real_metric")


def test_calculate_metric_wraps_invalid_arguments():
    with pytest.raises(MetricCalculationError, match="Invalid arguments"):
        calculate_metric("refund_rate", refund_count=1)  # missing total_order_count
