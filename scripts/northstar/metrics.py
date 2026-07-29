"""Shared deterministic measurements over generated data.

Used by ground_truth.py, evaluation_questions.py, and validate.py so the
"actual" numbers reported everywhere come from one computation, not three
independently hand-typed copies (ANALYTICS_ENGINE.md §1: numbers must come
from deterministic computation, not be invented in prose).
"""
from datetime import date
from typing import Any

from northstar.config import RAPIDSHIP, SWIFTSHIP, GeneratorConfig


def _split_by_incident(rows: list[dict[str, Any]], config: GeneratorConfig, date_field: str) -> tuple[list, list]:
    before = [r for r in rows if r[date_field].date() < config.incident_date]
    after = [r for r in rows if r[date_field].date() >= config.incident_date]
    return before, after


def rapidship_share(orders: list[dict], config: GeneratorConfig, after: bool) -> float:
    before, after_rows = _split_by_incident(orders, config, "order_date")
    subset = after_rows if after else before
    if not subset:
        return 0.0
    return sum(1 for o in subset if o["shipping_provider"] == RAPIDSHIP) / len(subset)


def average_delivery_days(orders: list[dict], provider: str, config: GeneratorConfig, after: bool) -> float | None:
    before, after_rows = _split_by_incident(orders, config, "order_date")
    subset = after_rows if after else before
    values = [o["delivery_days"] for o in subset if o["shipping_provider"] == provider and o["delivery_days"] is not None]
    if not values:
        return None
    return sum(values) / len(values)


def refund_rate(orders: list[dict], refunds: list[dict], config: GeneratorConfig, after: bool) -> float:
    before, after_rows = _split_by_incident(orders, config, "order_date")
    subset = after_rows if after else before
    if not subset:
        return 0.0
    order_ids = {o["order_id"] for o in subset}
    refund_count = sum(1 for r in refunds if r["order_id"] in order_ids)
    return refund_count / len(subset)


def late_delivery_refund_rate(orders: list[dict], refunds: list[dict], config: GeneratorConfig, after: bool) -> float:
    before, after_rows = _split_by_incident(orders, config, "order_date")
    subset = after_rows if after else before
    if not subset:
        return 0.0
    order_ids = {o["order_id"] for o in subset}
    late_refunds = sum(1 for r in refunds if r["order_id"] in order_ids and r["refund_reason"] == "late_delivery")
    return late_refunds / len(subset)


def shipping_ticket_share(tickets: list[dict], config: GeneratorConfig, after: bool) -> float:
    before, after_rows = _split_by_incident(tickets, config, "created_at")
    subset = after_rows if after else before
    if not subset:
        return 0.0
    return sum(1 for t in subset if t["category"] == "shipping") / len(subset)


def refund_reason_breakdown(refunds: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in refunds:
        counts[r["refund_reason"]] = counts.get(r["refund_reason"], 0) + 1
    return counts


def refunded_revenue(refunds: list[dict]) -> float:
    return round(sum(r["refund_amount"] for r in refunds if r["status"] == "completed"), 2)


def refund_rate_by_product(orders: list[dict], refunds: list[dict]) -> list[tuple[str, float, int]]:
    """Returns (product_id, refund_rate, order_count) sorted by refund_rate desc."""
    order_ids_by_product: dict[str, set[str]] = {}
    for o in orders:
        order_ids_by_product.setdefault(o["product_id"], set()).add(o["order_id"])

    refunded_order_ids = {r["order_id"] for r in refunds}

    results = []
    for product_id, order_ids in order_ids_by_product.items():
        refunded = len(order_ids & refunded_order_ids)
        results.append((product_id, refunded / len(order_ids), len(order_ids)))
    return sorted(results, key=lambda row: row[1], reverse=True)
