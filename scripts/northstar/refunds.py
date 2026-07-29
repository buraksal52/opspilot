"""Refund generation (BACKLOG.md 2.5, DATASET.md §13-14).

This is the module most directly responsible for the primary demo signal:
late-delivery refunds should spike for delayed orders (overwhelmingly
RapidShip, after the July 11 incident), while unrelated refund reasons keep
occurring at a roughly constant background rate regardless of date/provider.
"""
import random
from datetime import timedelta
from typing import Any

from northstar.config import GeneratorConfig
from northstar.ids import refund_id

NON_DELAY_REASONS: list[tuple[str, float]] = [
    ("damaged_product", 0.28),
    ("wrong_item", 0.14),
    ("product_quality", 0.24),
    ("changed_mind", 0.20),
    ("billing_issue", 0.08),
    ("other", 0.06),
]

REFUND_STATUS_WEIGHTS: list[tuple[str, float]] = [
    ("completed", 0.85),
    ("pending", 0.10),
    ("rejected", 0.05),
]


def _weighted_choice(rng: random.Random, weighted: list[tuple[str, float]]) -> str:
    items, weights = zip(*weighted)
    return rng.choices(items, weights=weights, k=1)[0]


def _late_delivery_refund_probability(delivery_days: int, config: GeneratorConfig) -> float:
    from northstar.config import DELAYED_THRESHOLD_DAYS

    overshoot = max(0, delivery_days - DELAYED_THRESHOLD_DAYS)
    probability = config.late_delivery_refund_base_probability + 0.03 * overshoot
    return min(probability, config.late_delivery_refund_probability_cap)


def generate_refunds(rng: random.Random, config: GeneratorConfig, orders: list[dict]) -> list[dict[str, Any]]:
    refunds = []
    counter = 1

    for order in orders:
        if order["order_status"] == "cancelled":
            continue  # cancelled orders are not refund candidates

        reason = None
        if order["is_delayed"] and rng.random() < _late_delivery_refund_probability(order["delivery_days"], config):
            reason = "late_delivery"
        elif rng.random() < config.baseline_refund_probability:
            reason = _weighted_choice(rng, NON_DELAY_REASONS)

        if reason is None:
            continue

        anchor = order["delivered_at"] or order["order_date"]
        requested_at = anchor + timedelta(days=rng.uniform(0, 5), hours=rng.uniform(0, 23))
        completed_at = requested_at + timedelta(days=rng.uniform(1, 4))

        refund_fraction = 1.0 if rng.random() < 0.85 else rng.uniform(0.4, 0.9)
        refund_amount = round(order["total_amount"] * refund_fraction, 2)

        refunds.append(
            {
                "refund_id": refund_id(counter),
                "order_id": order["order_id"],
                "customer_id": order["customer_id"],
                "refund_requested_at": requested_at,
                "refund_completed_at": completed_at,
                "refund_reason": reason,
                "refund_amount": refund_amount,
                "status": _weighted_choice(rng, REFUND_STATUS_WEIGHTS),
            }
        )
        counter += 1

    return refunds


def apply_refund_status_to_orders(orders: list[dict], refunds: list[dict]) -> None:
    """Reflect completed refunds back onto Order.order_status (DATASET.md §10)."""
    refunded_order_ids = {r["order_id"] for r in refunds if r["status"] == "completed"}
    for order in orders:
        if order["order_id"] in refunded_order_ids:
            order["order_status"] = "refunded"
