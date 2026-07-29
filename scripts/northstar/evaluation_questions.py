"""Canonical evaluation question bank (DATASET.md §33).

This is the single evaluation-question file for the whole project — RAG,
analytics, and agent evaluation (Phases 4/5/6+) all consume the
`retrieval`/`analytics`/`agent`/`e2e`-tagged subsets of this same file rather
than maintaining their own separate question sets.

Analytics questions carry `expected_value`, computed here from the actually
generated dataset (via northstar.metrics) rather than hand-typed targets, so
the expectation always matches what the generator actually produced.
"""
from typing import Any

from northstar.config import RAPIDSHIP, SWIFTSHIP, GeneratorConfig
from northstar import metrics


def _retrieval_questions() -> list[dict[str, Any]]:
    return [
        {
            "id": "retrieval-01",
            "question": "What is the standard delivery window?",
            "tags": ["retrieval"],
            "expected_document": "Shipping Policy",
            "expected_fact": "2-4 business days",
        },
        {
            "id": "retrieval-02",
            "question": "When did Northstar migrate shipping providers?",
            "tags": ["retrieval"],
            "expected_document": "Shipping Provider Migration Report",
            "expected_fact": "July 11",
        },
        {
            "id": "retrieval-03",
            "question": "What does the refund policy say about delayed deliveries?",
            "tags": ["retrieval"],
            "expected_document": "Refund Policy",
            "expected_fact": "replacement shipment or a full refund",
        },
        {
            "id": "retrieval-04",
            "question": "What is the escalation rule for urgent support tickets?",
            "tags": ["retrieval"],
            "expected_document": "Customer Support Handbook",
            "expected_fact": "within one business day",
        },
        {
            "id": "retrieval-05",
            "question": "Why was RapidShip selected as a shipping provider?",
            "tags": ["retrieval"],
            "expected_document": "Shipping Provider Migration Report",
            "expected_fact": "reduce Northstar Commerce's overall shipping cost by approximately 12%",
        },
    ]


def _analytics_questions(config: GeneratorConfig, orders: list[dict], refunds: list[dict], tickets: list[dict]) -> list[dict[str, Any]]:
    refund_rate_before = metrics.refund_rate(orders, refunds, config, after=False)
    refund_rate_after = metrics.refund_rate(orders, refunds, config, after=True)
    swiftship_days_after = metrics.average_delivery_days(orders, SWIFTSHIP, config, after=True)
    rapidship_days_after = metrics.average_delivery_days(orders, RAPIDSHIP, config, after=True)
    shipping_share_before = metrics.shipping_ticket_share(tickets, config, after=False)
    shipping_share_after = metrics.shipping_ticket_share(tickets, config, after=True)
    rapidship_share_after = metrics.rapidship_share(orders, config, after=True)
    top_product = metrics.refund_rate_by_product(orders, refunds)[0]

    return [
        {
            "id": "analytics-01",
            "question": "What was the refund rate before July 11?",
            "tags": ["analytics"],
            "expected_value": round(refund_rate_before, 4),
        },
        {
            "id": "analytics-02",
            "question": "What was the refund rate after July 11?",
            "tags": ["analytics"],
            "expected_value": round(refund_rate_after, 4),
        },
        {
            "id": "analytics-03",
            "question": "Compare RapidShip and SwiftShip average delivery times after July 11.",
            "tags": ["analytics"],
            "expected_value": {
                "rapidship_avg_days": round(rapidship_days_after, 2) if rapidship_days_after else None,
                "swiftship_avg_days": round(swiftship_days_after, 2) if swiftship_days_after else None,
            },
        },
        {
            "id": "analytics-04",
            "question": "What share of support tickets were shipping-related, before vs after July 11?",
            "tags": ["analytics"],
            "expected_value": {
                "before": round(shipping_share_before, 4),
                "after": round(shipping_share_after, 4),
            },
        },
        {
            "id": "analytics-05",
            "question": "Which product has the highest refund rate?",
            "tags": ["analytics", "agent"],
            "expected_value": {"product_id": top_product[0], "refund_rate": round(top_product[1], 4)},
        },
        {
            "id": "analytics-06",
            "question": "What percentage of orders after July 11 used RapidShip?",
            "tags": ["analytics"],
            "expected_value": round(rapidship_share_after, 4),
        },
        {
            "id": "analytics-07",
            "question": "What is the total refunded revenue?",
            "tags": ["analytics"],
            "expected_value": metrics.refunded_revenue(refunds),
        },
    ]


def _agent_questions() -> list[dict[str, Any]]:
    return [
        {
            "id": "agent-01",
            "question": "Why did refunds increase this month?",
            "tags": ["agent", "e2e"],
            "expected_behavior": [
                "confirms refunds increased",
                "identifies the increase beginning around July 11",
                "identifies late-delivery as a driving refund reason",
                "connects the increase to RapidShip delivery performance",
                "cites the Shipping Provider Migration Report as supporting evidence",
                "does not invent unsupported numerical claims",
            ],
        },
        {
            "id": "agent-02",
            "question": "Which customer segment was most affected?",
            "tags": ["agent"],
            "expected_behavior": [
                "segments customers by customer_segment",
                "measures delayed orders/refunds/tickets per segment",
                "supports its claim with a computed comparison, not a guess",
            ],
        },
        {
            "id": "agent-03",
            "question": "What changed around July 11?",
            "tags": ["agent"],
            "expected_behavior": [
                "identifies the shipping provider migration date",
                "references the Shipping Provider Migration Report",
                "connects the date to a measurable change in delivery metrics",
            ],
        },
        {
            "id": "agent-04",
            "question": "How much revenue is at risk from the refund increase?",
            "tags": ["agent"],
            "expected_behavior": [
                "reports refunded revenue as an exact observed value",
                "clearly labels any repeat-purchase-decline estimate as an estimate, not an exact figure",
                "does not present an estimate as if it were an exact observed value",
            ],
        },
        {
            "id": "agent-05",
            "question": "Which products have the highest refund rate?",
            "tags": ["agent", "analytics"],
            "expected_behavior": [
                "uses structured analytics (query_database/calculate_metric) rather than guessing",
                "ranks products by computed refund rate",
            ],
        },
        {
            "id": "agent-06",
            "question": "What should Northstar do next?",
            "tags": ["agent"],
            "expected_behavior": [
                "recommendations are each connected to a specific finding",
                "at least one recommendation references RapidShip/shipping performance",
                "does not recommend actions unsupported by any finding",
            ],
        },
    ]


def build_evaluation_questions(
    config: GeneratorConfig, orders: list[dict], refunds: list[dict], support_tickets: list[dict]
) -> list[dict[str, Any]]:
    questions = (
        _retrieval_questions()
        + _analytics_questions(config, orders, refunds, support_tickets)
        + _agent_questions()
    )
    assert 15 <= len(questions) <= 25, "DATASET.md §33 requires 15-25 canonical evaluation questions"

    valid_tags = {"retrieval", "analytics", "agent", "e2e"}
    for q in questions:
        assert set(q["tags"]) <= valid_tags, f"invalid tag on {q['id']}"

    return questions
