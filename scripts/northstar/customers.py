"""Customer generation (BACKLOG.md 2.2, DATASET.md §8)."""
import random
from datetime import date, datetime, time, timedelta, UTC
from typing import Any

from northstar.config import GeneratorConfig
from northstar.ids import customer_id

COUNTRIES_CITIES: list[tuple[str, str]] = [
    ("United States", "New York"),
    ("United States", "Austin"),
    ("United States", "Seattle"),
    ("United States", "Chicago"),
    ("United States", "Denver"),
    ("Canada", "Toronto"),
    ("Canada", "Vancouver"),
    ("United Kingdom", "London"),
    ("United Kingdom", "Manchester"),
    ("Germany", "Berlin"),
    ("Germany", "Munich"),
    ("Australia", "Sydney"),
]

SEGMENT_WEIGHTS: list[tuple[str, float]] = [
    ("new", 0.40),
    ("regular", 0.45),
    ("high_value", 0.15),
]

CHANNEL_WEIGHTS: list[tuple[str, float]] = [
    ("organic", 0.30),
    ("paid_search", 0.25),
    ("social", 0.20),
    ("referral", 0.15),
    ("email", 0.10),
]


def _weighted_choice(rng: random.Random, weighted: list[tuple[str, float]]) -> str:
    items, weights = zip(*weighted)
    return rng.choices(items, weights=weights, k=1)[0]


def _random_utc_datetime(rng: random.Random, start: date, end: date) -> datetime:
    span_days = (end - start).days
    offset_days = rng.randint(0, max(span_days, 0))
    offset_seconds = rng.randint(0, 86399)
    return datetime.combine(start, time.min, tzinfo=UTC) + timedelta(days=offset_days, seconds=offset_seconds)


def generate_customers(rng: random.Random, config: GeneratorConfig) -> list[dict[str, Any]]:
    """Generate customer identity/segmentation records.

    `lifetime_orders` / `lifetime_value` start at zero and are filled in by
    `apply_customer_lifetime_metrics` once orders exist, so they reflect real
    generated behavior rather than being independently fabricated.
    """
    lookback_start = config.start_date - timedelta(days=730)
    customers = []
    for i in range(1, config.customer_count + 1):
        country, city = rng.choice(COUNTRIES_CITIES)
        customers.append(
            {
                "customer_id": customer_id(i),
                "created_at": _random_utc_datetime(rng, lookback_start, config.end_date),
                "country": country,
                "city": city,
                "customer_segment": _weighted_choice(rng, SEGMENT_WEIGHTS),
                "acquisition_channel": _weighted_choice(rng, CHANNEL_WEIGHTS),
                "lifetime_orders": 0,
                "lifetime_value": 0.0,
            }
        )
    return customers


def apply_customer_lifetime_metrics(
    customers: list[dict[str, Any]], orders: list[dict[str, Any]]
) -> None:
    """Derive lifetime_orders/lifetime_value from actual generated orders (in place)."""
    totals: dict[str, tuple[int, float]] = {}
    for order in orders:
        count, value = totals.get(order["customer_id"], (0, 0.0))
        totals[order["customer_id"]] = (count + 1, value + order["total_amount"])

    for customer in customers:
        count, value = totals.get(customer["customer_id"], (0, 0.0))
        customer["lifetime_orders"] = count
        customer["lifetime_value"] = round(value, 2)
