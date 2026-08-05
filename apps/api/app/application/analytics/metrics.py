"""Deterministic metric calculations (ANALYTICS_ENGINE.md §16-17/§24,
AGENT_SYSTEM.md §13, BACKLOG.md 5.7).

These are the internal functions `calculate_metric` (the single agent-facing
tool, AGENT_SYSTEM.md §13) dispatches to. They are pure arithmetic over
values already produced by SQL execution (`AnalyticsQueryExecutor`) — they
never query the database themselves, and the LLM never performs this
arithmetic in prose (ANALYTICS_ENGINE.md §15).
"""
from dataclasses import dataclass


class MetricCalculationError(Exception):
    """Raised for invalid inputs (e.g. division by zero) rather than
    returning a fabricated or silently wrong number (ANALYTICS_ENGINE.md §19)."""


@dataclass(frozen=True, slots=True)
class PercentageChangeResult:
    absolute_change: float
    relative_change_percent: float | None
    # Only meaningful when `before`/`after` are themselves rates (e.g. 0.04 ->
    # 0.05); None otherwise (ANALYTICS_ENGINE.md §17 — never mix these silently).
    percentage_point_change: float | None


@dataclass(frozen=True, slots=True)
class RevenueImpactResult:
    directly_refunded_revenue: float
    estimated_repeat_purchase_risk: float | None
    total_estimated_impact: float
    methodology: str


def calculate_percentage_change(before: float, after: float, *, as_rate: bool = False) -> PercentageChangeResult:
    """ANALYTICS_ENGINE.md §17 example: 4% -> 5% is a 1 percentage-point
    absolute increase but a 25% relative increase. `as_rate=True` populates
    `percentage_point_change`; it is meaningless for non-rate metrics (e.g.
    plain revenue) and left None otherwise."""
    absolute_change = after - before
    relative_change_percent = (absolute_change / before * 100) if before != 0 else None
    percentage_point_change = absolute_change * 100 if as_rate else None
    return PercentageChangeResult(
        absolute_change=absolute_change,
        relative_change_percent=relative_change_percent,
        percentage_point_change=percentage_point_change,
    )


def calculate_refund_rate(refund_count: int, total_order_count: int) -> float:
    if total_order_count <= 0:
        raise MetricCalculationError("Cannot calculate a refund rate with zero or negative total orders.")
    if refund_count < 0:
        raise MetricCalculationError("refund_count cannot be negative.")
    return refund_count / total_order_count


def calculate_average_delivery_time(delivery_days: list[float]) -> float:
    if not delivery_days:
        raise MetricCalculationError("Cannot calculate an average delivery time with no delivery observations.")
    return sum(delivery_days) / len(delivery_days)


def calculate_revenue_impact(
    directly_refunded_revenue: float, estimated_repeat_purchase_risk: float | None = None
) -> RevenueImpactResult:
    """ANALYTICS_ENGINE.md §24 — exact observed value plus an optional,
    clearly-labeled estimate component; never presented as a single
    undifferentiated number."""
    if directly_refunded_revenue < 0:
        raise MetricCalculationError("directly_refunded_revenue cannot be negative.")

    total = directly_refunded_revenue + (estimated_repeat_purchase_risk or 0.0)
    methodology = f"Total estimated impact = directly refunded revenue (${directly_refunded_revenue:,.2f}, observed)"
    if estimated_repeat_purchase_risk is not None:
        methodology += f" + estimated repeat-purchase risk (${estimated_repeat_purchase_risk:,.2f}, estimate)"
    return RevenueImpactResult(
        directly_refunded_revenue=directly_refunded_revenue,
        estimated_repeat_purchase_risk=estimated_repeat_purchase_risk,
        total_estimated_impact=total,
        methodology=methodology,
    )


_METRIC_FUNCTIONS = {
    "percentage_change": calculate_percentage_change,
    "refund_rate": calculate_refund_rate,
    "average_delivery_time": calculate_average_delivery_time,
    "revenue_impact": calculate_revenue_impact,
}


def calculate_metric(metric_type: str, **kwargs) -> object:
    """Dispatch used by the single agent-facing `calculate_metric` tool
    (AGENT_SYSTEM.md §13) — the agent never calls the functions above
    directly, only this dispatcher by name."""
    func = _METRIC_FUNCTIONS.get(metric_type)
    if func is None:
        raise MetricCalculationError(
            f"Unknown metric_type '{metric_type}'. Supported: {', '.join(sorted(_METRIC_FUNCTIONS))}."
        )
    try:
        return func(**kwargs)
    except TypeError as exc:
        raise MetricCalculationError(f"Invalid arguments for metric '{metric_type}': {exc}") from exc
