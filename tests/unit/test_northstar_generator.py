"""Unit tests for the Northstar dataset generator (TESTING.md §7, BACKLOG.md 2.9).

Runs the real generator (fast, pure Python, no I/O) and asserts the
deterministic properties DATASET.md/BACKLOG.md require: reproducibility,
referential integrity, expected row-count ranges, and the incident-driven
patterns (RapidShip timing, delivery-time increase, refund increase, ticket
increase) the whole demo depends on.
"""
from northstar.config import DEFAULT_CONFIG, DELAYED_THRESHOLD_DAYS, RAPIDSHIP, SWIFTSHIP
from northstar.evaluation_questions import build_evaluation_questions
from northstar.generate import generate_all
from northstar.ground_truth import build_ground_truth
from northstar import metrics
from northstar.validate import validate_dataset


def test_generation_is_deterministic_for_a_fixed_seed():
    first = generate_all(DEFAULT_CONFIG)
    second = generate_all(DEFAULT_CONFIG)

    assert first["orders"] == second["orders"]
    assert first["customers"] == second["customers"]
    assert first["refunds"] == second["refunds"]
    assert first["support_tickets"] == second["support_tickets"]


def test_full_dataset_passes_validation():
    dataset = generate_all(DEFAULT_CONFIG)
    report = validate_dataset(
        DEFAULT_CONFIG,
        dataset["customers"],
        dataset["products"],
        dataset["orders"],
        dataset["refunds"],
        dataset["support_tickets"],
    )

    failed = [c.name for c in report.checks if not c.passed]
    assert report.passed, f"validation failed: {failed}"
    assert len(report.checks) >= 14


def test_foreign_keys_are_consistent():
    dataset = generate_all(DEFAULT_CONFIG)
    customer_ids = {c["customer_id"] for c in dataset["customers"]}
    product_ids = {p["product_id"] for p in dataset["products"]}
    order_ids = {o["order_id"] for o in dataset["orders"]}

    assert all(o["customer_id"] in customer_ids for o in dataset["orders"])
    assert all(o["product_id"] in product_ids for o in dataset["orders"])
    assert all(r["order_id"] in order_ids for r in dataset["refunds"])
    assert all(
        t["order_id"] is None or t["order_id"] in order_ids for t in dataset["support_tickets"]
    )


def test_row_counts_are_within_dataset_md_targets():
    dataset = generate_all(DEFAULT_CONFIG)
    assert 2900 <= len(dataset["customers"]) <= 3100
    assert 80 <= len(dataset["products"]) <= 120
    assert 14900 <= len(dataset["orders"]) <= 15100
    assert 700 <= len(dataset["refunds"]) <= 900
    assert 1900 <= len(dataset["support_tickets"]) <= 2100


def test_is_delayed_uses_the_documented_threshold():
    dataset = generate_all(DEFAULT_CONFIG)
    for order in dataset["orders"]:
        if order["delivery_days"] is None:
            assert order["is_delayed"] is False
        else:
            assert order["is_delayed"] == (order["delivery_days"] > DELAYED_THRESHOLD_DAYS)
    assert DELAYED_THRESHOLD_DAYS == 4


def test_rapidship_share_shifts_around_the_incident_date():
    dataset = generate_all(DEFAULT_CONFIG)
    before = metrics.rapidship_share(dataset["orders"], DEFAULT_CONFIG, after=False)
    after = metrics.rapidship_share(dataset["orders"], DEFAULT_CONFIG, after=True)

    assert before < 0.10
    assert 0.55 <= after <= 0.80
    assert after > before


def test_delivery_time_increases_for_rapidship_after_incident():
    dataset = generate_all(DEFAULT_CONFIG)
    swiftship_after = metrics.average_delivery_days(dataset["orders"], SWIFTSHIP, DEFAULT_CONFIG, after=True)
    rapidship_after = metrics.average_delivery_days(dataset["orders"], RAPIDSHIP, DEFAULT_CONFIG, after=True)

    assert rapidship_after > swiftship_after
    assert 4.0 <= rapidship_after <= 5.5


def test_refund_rate_increases_after_incident_but_not_perfectly():
    dataset = generate_all(DEFAULT_CONFIG)
    before = metrics.refund_rate(dataset["orders"], dataset["refunds"], DEFAULT_CONFIG, after=False)
    after = metrics.refund_rate(dataset["orders"], dataset["refunds"], DEFAULT_CONFIG, after=True)

    assert after > before

    # DATASET.md §6: the relationship must not be perfect — some refunds after
    # the incident must still be unrelated to late delivery.
    after_incident_order_ids = {
        o["order_id"] for o in dataset["orders"] if o["order_date"].date() >= DEFAULT_CONFIG.incident_date
    }
    non_late_after = [
        r for r in dataset["refunds"] if r["order_id"] in after_incident_order_ids and r["refund_reason"] != "late_delivery"
    ]
    assert len(non_late_after) > 0


def test_shipping_ticket_share_increases_after_incident():
    dataset = generate_all(DEFAULT_CONFIG)
    before = metrics.shipping_ticket_share(dataset["support_tickets"], DEFAULT_CONFIG, after=False)
    after = metrics.shipping_ticket_share(dataset["support_tickets"], DEFAULT_CONFIG, after=True)

    assert after > before
    relative_change = (after - before) / before * 100
    assert 20.0 <= relative_change <= 80.0


def test_evaluation_question_bank_matches_dataset_md_format():
    dataset = generate_all(DEFAULT_CONFIG)
    questions = build_evaluation_questions(
        DEFAULT_CONFIG, dataset["orders"], dataset["refunds"], dataset["support_tickets"]
    )

    assert 15 <= len(questions) <= 25
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "question ids must be unique"

    valid_tags = {"retrieval", "analytics", "agent", "e2e"}
    for question in questions:
        assert set(question["tags"]) <= valid_tags
        assert question["tags"], f"{question['id']} has no tags"

    tags_present = {tag for q in questions for tag in q["tags"]}
    assert {"retrieval", "analytics", "agent", "e2e"} <= tags_present


def test_ground_truth_reflects_the_actually_generated_data():
    dataset = generate_all(DEFAULT_CONFIG)
    ground_truth = build_ground_truth(
        DEFAULT_CONFIG, dataset["orders"], dataset["refunds"], dataset["support_tickets"]
    )

    assert ground_truth["primary_incident"]["date"] == DEFAULT_CONFIG.incident_date.isoformat()
    assert ground_truth["primary_incident"]["provider"] == RAPIDSHIP

    expected_refund_rate_after = metrics.refund_rate(dataset["orders"], dataset["refunds"], DEFAULT_CONFIG, after=True)
    assert ground_truth["measured_values"]["refund_rate_after"] == round(expected_refund_rate_after, 4)


def test_customer_lifetime_metrics_are_derived_from_orders():
    dataset = generate_all(DEFAULT_CONFIG)
    orders_by_customer: dict[str, list[dict]] = {}
    for order in dataset["orders"]:
        orders_by_customer.setdefault(order["customer_id"], []).append(order)

    checked = 0
    for customer in dataset["customers"]:
        customer_orders = orders_by_customer.get(customer["customer_id"], [])
        assert customer["lifetime_orders"] == len(customer_orders)
        if customer_orders:
            checked += 1
    assert checked > 0
