"""Support ticket generation (BACKLOG.md 2.6, DATASET.md §15-17).

Ticket dates are sampled uniformly across the whole window, and only the
*category weighting* shifts after the incident date. Because the total daily
ticket rate stays roughly constant, a higher post-incident shipping-category
share also produces a higher post-incident shipping-ticket per-day rate,
which is what DATASET.md §5 actually asks for.
"""
import random
from datetime import timedelta
from typing import Any

from northstar.config import GeneratorConfig
from northstar.ids import ticket_id

CATEGORY_WEIGHTS_BEFORE: dict[str, float] = {
    "shipping": 0.17,
    "refund": 0.15,
    "product_issue": 0.22,
    "billing": 0.16,
    "account": 0.12,
    "general": 0.18,
}

CHANNEL_WEIGHTS: list[tuple[str, float]] = [("email", 0.45), ("chat", 0.35), ("web", 0.20)]
PRIORITY_WEIGHTS: list[tuple[str, float]] = [("low", 0.30), ("medium", 0.40), ("high", 0.22), ("urgent", 0.08)]
STATUS_WEIGHTS: list[tuple[str, float]] = [("resolved", 0.55), ("closed", 0.35), ("open", 0.10)]

SHIPPING_SUBJECTS = [
    "Order still hasn't arrived",
    "Delivery is taking much longer than expected",
    "Tracking hasn't updated in days",
    "Where is my package?",
    "Requesting cancellation due to delay",
    "Refund request for late delivery",
]
SHIPPING_BODIES = [
    "My order {order_id} was supposed to arrive within a few days, but it still hasn't shown up. Can you check the status?",
    "The tracking page for order {order_id} hasn't moved in a while. I'm getting worried it's lost.",
    "It has been over a week since I placed order {order_id} and delivery keeps getting pushed back.",
    "I expected order {order_id} much sooner based on the shipping estimate. This delay is frustrating.",
    "Can someone look into order {order_id}? The delivery date has already passed.",
]

REFUND_SUBJECTS = ["Refund status question", "Requesting a refund", "Haven't received my refund yet"]
REFUND_BODIES = [
    "I'm following up on the refund for order {order_id}. Can you confirm when it will be processed?",
    "I requested a refund for order {order_id} and wanted to check on the timeline.",
    "Order {order_id} qualifies for a refund based on your policy — please advise on next steps.",
]

PRODUCT_SUBJECTS = ["Item arrived damaged", "Product doesn't work as expected", "Wrong item received"]
PRODUCT_BODIES = [
    "The item from order {order_id} arrived with visible damage. Can I get a replacement?",
    "The product from order {order_id} stopped working after a couple of days.",
    "I received the wrong item for order {order_id} — expected something different.",
]

BILLING_SUBJECTS = ["Question about my charge", "Billing discrepancy", "Duplicate charge on my card"]
BILLING_BODIES = [
    "I noticed a charge for order {order_id} that doesn't match what I expected to pay.",
    "Can you clarify the billing breakdown for order {order_id}?",
    "It looks like I may have been charged twice for order {order_id}.",
]

ACCOUNT_SUBJECTS = ["Can't log into my account", "Need to update my account details", "Account locked"]
ACCOUNT_BODIES = [
    "I'm unable to sign in to my account even after resetting my password.",
    "I'd like to update the email address associated with my account.",
    "My account seems to be locked and I'm not sure why.",
]

GENERAL_SUBJECTS = ["General question about a product", "Question before placing an order", "Feedback on my experience"]
GENERAL_BODIES = [
    "I have a quick question about one of your products before I order.",
    "Just wanted to share some feedback about my recent experience shopping with you.",
    "Do you have more details available about product availability?",
]

CATEGORY_CONTENT: dict[str, tuple[list[str], list[str]]] = {
    "shipping": (SHIPPING_SUBJECTS, SHIPPING_BODIES),
    "refund": (REFUND_SUBJECTS, REFUND_BODIES),
    "product_issue": (PRODUCT_SUBJECTS, PRODUCT_BODIES),
    "billing": (BILLING_SUBJECTS, BILLING_BODIES),
    "account": (ACCOUNT_SUBJECTS, ACCOUNT_BODIES),
    "general": (GENERAL_SUBJECTS, GENERAL_BODIES),
}


def _weighted_choice(rng: random.Random, weighted: list[tuple[str, float]]) -> str:
    items, weights = zip(*weighted)
    return rng.choices(items, weights=weights, k=1)[0]


def _category_weights_for_date(config: GeneratorConfig, is_post_incident: bool) -> dict[str, float]:
    if not is_post_incident:
        return CATEGORY_WEIGHTS_BEFORE

    boosted_shipping = CATEGORY_WEIGHTS_BEFORE["shipping"] * (1 + config.shipping_ticket_share_relative_increase)
    remaining_categories = {k: v for k, v in CATEGORY_WEIGHTS_BEFORE.items() if k != "shipping"}
    remaining_total_before = sum(remaining_categories.values())
    remaining_total_after = 1 - boosted_shipping
    scale = remaining_total_after / remaining_total_before

    weights = {k: v * scale for k, v in remaining_categories.items()}
    weights["shipping"] = boosted_shipping
    return weights


def _random_order_datetime(rng: random.Random, config: GeneratorConfig):
    from datetime import datetime, time, UTC

    span_days = (config.end_date - config.start_date).days
    offset_days = rng.randint(0, span_days)
    offset_seconds = rng.randint(0, 86399)
    return datetime.combine(config.start_date, time.min, tzinfo=UTC) + timedelta(days=offset_days, seconds=offset_seconds)


def generate_support_tickets(
    rng: random.Random, config: GeneratorConfig, customers: list[dict], orders: list[dict]
) -> list[dict[str, Any]]:
    delayed_post_incident_orders = [
        o for o in orders if o["is_delayed"] and o["order_date"].date() >= config.incident_date
    ]
    all_orders_by_customer: dict[str, list[dict]] = {}
    for order in orders:
        all_orders_by_customer.setdefault(order["customer_id"], []).append(order)

    tickets = []
    for i in range(1, config.ticket_count + 1):
        created_at = _random_order_datetime(rng, config)
        is_post_incident = created_at.date() >= config.incident_date

        weights = _category_weights_for_date(config, is_post_incident)
        category = rng.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]

        # Link shipping tickets to a genuinely delayed order where possible so the
        # ticket text and the underlying order data tell the same story.
        order = None
        if category == "shipping" and is_post_incident and delayed_post_incident_orders and rng.random() < 0.7:
            order = rng.choice(delayed_post_incident_orders)
        elif rng.random() < 0.85:
            order = rng.choice(orders)

        customer_id = order["customer_id"] if order else rng.choice(customers)["customer_id"]

        subjects, bodies = CATEGORY_CONTENT[category]
        subject = rng.choice(subjects)
        body_template = rng.choice(bodies)
        message = body_template.format(order_id=order["order_id"] if order else "N/A")

        is_shipping_delay_ticket = category == "shipping" and order is not None and order.get("is_delayed")
        sentiment_weights = (
            [("positive", 0.05), ("neutral", 0.25), ("negative", 0.70)]
            if is_shipping_delay_ticket
            else [("positive", 0.25), ("neutral", 0.50), ("negative", 0.25)]
        )

        tickets.append(
            {
                "ticket_id": ticket_id(i),
                "customer_id": customer_id,
                "order_id": order["order_id"] if order else None,
                "created_at": created_at,
                "category": category,
                "priority": _weighted_choice(rng, PRIORITY_WEIGHTS),
                "channel": _weighted_choice(rng, CHANNEL_WEIGHTS),
                "subject": subject,
                "message": message,
                "status": _weighted_choice(rng, STATUS_WEIGHTS),
                "resolution_time_hours": round(max(0.5, rng.gauss(18, 12)), 1),
                "sentiment": _weighted_choice(rng, sentiment_weights),
            }
        )
    return tickets
