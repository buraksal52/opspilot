"""Order generation — the primary commerce/delivery dataset (BACKLOG.md 2.4, DATASET.md §10-12)."""
import random
from datetime import date, datetime, time, timedelta, UTC
from typing import Any

from northstar.config import DELAYED_THRESHOLD_DAYS, RAPIDSHIP, SWIFTSHIP, GeneratorConfig
from northstar.ids import order_id

ORDER_STATUSES_TERMINAL = ["delivered", "cancelled"]


def _random_order_datetime(rng: random.Random, start: date, end: date) -> datetime:
    span_days = (end - start).days
    offset_days = rng.randint(0, span_days)
    offset_seconds = rng.randint(0, 86399)
    return datetime.combine(start, time.min, tzinfo=UTC) + timedelta(days=offset_days, seconds=offset_seconds)


def _choose_provider(rng: random.Random, order_date: datetime, config: GeneratorConfig) -> str:
    is_post_incident = order_date.date() >= config.incident_date
    share = config.rapidship_share_after if is_post_incident else config.rapidship_share_before
    return RAPIDSHIP if rng.random() < share else SWIFTSHIP


def _sample_delivery_days(rng: random.Random, provider: str, is_post_incident: bool, config: GeneratorConfig) -> int:
    if provider == SWIFTSHIP:
        days = rng.gauss(config.swiftship_mean_days, config.swiftship_stdev_days)
    else:
        if is_post_incident and rng.random() < config.rapidship_severe_probability:
            days = rng.gauss(config.rapidship_severe_mean_days, config.rapidship_severe_stdev_days)
        elif is_post_incident:
            days = rng.gauss(config.rapidship_normal_mean_days, config.rapidship_normal_stdev_days)
        else:
            # DATASET.md §6: a handful of pre-incident RapidShip orders exist too,
            # and behave like normal traffic since the operational issues had not
            # started yet.
            days = rng.gauss(config.swiftship_mean_days, config.swiftship_stdev_days)
    return max(1, round(days))


def generate_orders(rng: random.Random, config: GeneratorConfig, customers: list[dict], products: list[dict]) -> list[dict[str, Any]]:
    customer_ids = [c["customer_id"] for c in customers]
    active_products = [p for p in products if p["active"]] or products

    orders = []
    for i in range(1, config.order_count + 1):
        order_date = _random_order_datetime(rng, config.start_date, config.end_date)
        is_post_incident = order_date.date() >= config.incident_date

        provider = _choose_provider(rng, order_date, config)
        product = rng.choice(active_products)
        quantity = rng.choices([1, 2, 3], weights=[0.75, 0.18, 0.07], k=1)[0]

        # Small handling delay between order placement and shipment.
        shipped_at = order_date + timedelta(hours=rng.uniform(2, 30))
        delivery_days = _sample_delivery_days(rng, provider, is_post_incident, config)
        projected_delivered_at = shipped_at + timedelta(days=delivery_days)

        cancelled = rng.random() < 0.02
        if cancelled:
            status = "cancelled"
            delivered_at = None
        elif projected_delivered_at.date() > config.end_date:
            # Placed too close to the end of the observed window to have arrived yet.
            status = "in_transit"
            delivered_at = None
        else:
            status = "delivered"
            delivered_at = projected_delivered_at

        is_delayed = delivered_at is not None and delivery_days > DELAYED_THRESHOLD_DAYS

        orders.append(
            {
                "order_id": order_id(i),
                "customer_id": rng.choice(customer_ids),
                "product_id": product["product_id"],
                "order_date": order_date,
                "shipped_at": shipped_at,
                "delivered_at": delivered_at,
                "shipping_provider": provider,
                "quantity": quantity,
                "unit_price": product["unit_price"],
                "total_amount": round(product["unit_price"] * quantity, 2),
                "order_status": status,
                "delivery_days": delivery_days if delivered_at is not None else None,
                "is_delayed": is_delayed,
            }
        )
    return orders
