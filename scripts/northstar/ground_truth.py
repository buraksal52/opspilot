"""Ground truth generation (BACKLOG.md 2.8, DATASET.md §28).

This file is a private development/evaluation artifact. Per DATASET.md §28,
the runtime application (ingestion, retrieval, analytics, the agent) must
never read ground_truth.json as a knowledge source — it exists only for
offline evaluation, testing, and debugging.
"""
from typing import Any

from northstar.config import RAPIDSHIP, SWIFTSHIP, GeneratorConfig
from northstar import metrics


def build_ground_truth(
    config: GeneratorConfig,
    orders: list[dict],
    refunds: list[dict],
    support_tickets: list[dict],
) -> dict[str, Any]:
    refund_rate_before = metrics.refund_rate(orders, refunds, config, after=False)
    refund_rate_after = metrics.refund_rate(orders, refunds, config, after=True)

    shipping_share_before = metrics.shipping_ticket_share(support_tickets, config, after=False)
    shipping_share_after = metrics.shipping_ticket_share(support_tickets, config, after=True)

    swiftship_days_before = metrics.average_delivery_days(orders, SWIFTSHIP, config, after=False)
    rapidship_days_after = metrics.average_delivery_days(orders, RAPIDSHIP, config, after=True)

    return {
        "primary_incident": {
            "date": config.incident_date.isoformat(),
            "event": "shipping_provider_migration",
            "previous_provider": SWIFTSHIP,
            "provider": RAPIDSHIP,
        },
        "expected_patterns": {
            "delivery_time": "increase",
            "shipping_tickets": "increase",
            "refunds": "increase",
        },
        "measured_values": {
            "note": "Computed from the actually generated dataset, not hand-picked targets.",
            "refund_rate_before": round(refund_rate_before, 4),
            "refund_rate_after": round(refund_rate_after, 4),
            "refund_rate_relative_change_percent": round(
                _relative_change_percent(refund_rate_before, refund_rate_after), 2
            ),
            "shipping_ticket_share_before": round(shipping_share_before, 4),
            "shipping_ticket_share_after": round(shipping_share_after, 4),
            "shipping_ticket_share_relative_change_percent": round(
                _relative_change_percent(shipping_share_before, shipping_share_after), 2
            ),
            "avg_delivery_days_swiftship_before": round(swiftship_days_before, 2) if swiftship_days_before else None,
            "avg_delivery_days_rapidship_after": round(rapidship_days_after, 2) if rapidship_days_after else None,
            "rapidship_share_before": round(metrics.rapidship_share(orders, config, after=False), 4),
            "rapidship_share_after": round(metrics.rapidship_share(orders, config, after=True), 4),
        },
        "dataset_period": {
            "start_date": config.start_date.isoformat(),
            "end_date": config.end_date.isoformat(),
        },
        "seed": config.seed,
    }


def _relative_change_percent(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return ((after - before) / before) * 100
