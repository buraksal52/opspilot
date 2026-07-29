"""Deterministic dataset validation (BACKLOG.md 2.9, DATASET.md §30-31).

"If these checks fail, the generated dataset should not be accepted."
`assert_dataset_valid` enforces exactly that: generate.py refuses to write
output (or write it as accepted) if any check here fails.
"""
from dataclasses import dataclass, field
from typing import Any

from northstar.config import RAPIDSHIP, SWIFTSHIP, GeneratorConfig
from northstar import metrics


@dataclass
class ValidationCheck:
    name: str
    passed: bool
    detail: str
    measured: Any = None


@dataclass
class ValidationReport:
    checks: list[ValidationCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail, "measured": c.measured}
                for c in self.checks
            ],
        }


def _check_foreign_keys(
    report: ValidationReport,
    customers: list[dict],
    products: list[dict],
    orders: list[dict],
    refunds: list[dict],
    support_tickets: list[dict],
) -> None:
    customer_ids = {c["customer_id"] for c in customers}
    product_ids = {p["product_id"] for p in products}
    order_ids = {o["order_id"] for o in orders}
    orders_by_id = {o["order_id"]: o for o in orders}

    bad_order_customers = [o["order_id"] for o in orders if o["customer_id"] not in customer_ids]
    report.checks.append(
        ValidationCheck(
            "orders.customer_id -> customers.customer_id",
            not bad_order_customers,
            "all orders reference an existing customer" if not bad_order_customers else f"{len(bad_order_customers)} orphan orders",
            len(bad_order_customers),
        )
    )

    bad_order_products = [o["order_id"] for o in orders if o["product_id"] not in product_ids]
    report.checks.append(
        ValidationCheck(
            "orders.product_id -> products.product_id",
            not bad_order_products,
            "all orders reference an existing product" if not bad_order_products else f"{len(bad_order_products)} orphan orders",
            len(bad_order_products),
        )
    )

    bad_refund_orders = [r["refund_id"] for r in refunds if r["order_id"] not in order_ids]
    report.checks.append(
        ValidationCheck(
            "refunds.order_id -> orders.order_id (no orphan refunds)",
            not bad_refund_orders,
            "all refunds reference an existing order" if not bad_refund_orders else f"{len(bad_refund_orders)} orphan refunds",
            len(bad_refund_orders),
        )
    )

    bad_refund_customers = [
        r["refund_id"] for r in refunds if orders_by_id[r["order_id"]]["customer_id"] != r["customer_id"]
    ]
    report.checks.append(
        ValidationCheck(
            "refunds.customer_id matches refunds.order_id's customer",
            not bad_refund_customers,
            "consistent" if not bad_refund_customers else f"{len(bad_refund_customers)} mismatched refunds",
            len(bad_refund_customers),
        )
    )

    bad_ticket_customers = [t["ticket_id"] for t in support_tickets if t["customer_id"] not in customer_ids]
    bad_ticket_orders = [
        t["ticket_id"] for t in support_tickets if t["order_id"] is not None and t["order_id"] not in order_ids
    ]
    report.checks.append(
        ValidationCheck(
            "support_tickets.customer_id -> customers.customer_id",
            not bad_ticket_customers,
            "all tickets reference an existing customer" if not bad_ticket_customers else f"{len(bad_ticket_customers)} orphan tickets",
            len(bad_ticket_customers),
        )
    )
    report.checks.append(
        ValidationCheck(
            "support_tickets.order_id -> orders.order_id (or null)",
            not bad_ticket_orders,
            "all non-null ticket order references exist" if not bad_ticket_orders else f"{len(bad_ticket_orders)} orphan ticket order refs",
            len(bad_ticket_orders),
        )
    )


def _check_row_counts(
    report: ValidationReport, customers: list[dict], products: list[dict], orders: list[dict], refunds: list[dict], support_tickets: list[dict]
) -> None:
    def _range_check(name: str, count: int, low: int, high: int) -> None:
        report.checks.append(
            ValidationCheck(name, low <= count <= high, f"expected [{low}, {high}], got {count}", count)
        )

    _range_check("customers.csv row count ~3,000", len(customers), 2900, 3100)
    _range_check("products.csv row count 80-120", len(products), 80, 120)
    _range_check("orders.csv row count ~15,000", len(orders), 14900, 15100)
    _range_check("refunds.csv row count 700-900", len(refunds), 700, 900)
    _range_check("support_tickets.csv row count ~2,000", len(support_tickets), 1900, 2100)


def _check_incident_patterns(
    report: ValidationReport, config: GeneratorConfig, orders: list[dict], refunds: list[dict], support_tickets: list[dict]
) -> None:
    rapidship_before = metrics.rapidship_share(orders, config, after=False)
    rapidship_after = metrics.rapidship_share(orders, config, after=True)
    report.checks.append(
        ValidationCheck(
            "RapidShip traffic begins around the migration date",
            rapidship_before < 0.10 and 0.55 <= rapidship_after <= 0.80,
            f"before={rapidship_before:.3f} (want <0.10), after={rapidship_after:.3f} (want 0.55-0.80)",
            {"before": rapidship_before, "after": rapidship_after},
        )
    )

    swiftship_after = metrics.average_delivery_days(orders, SWIFTSHIP, config, after=True)
    rapidship_days_after = metrics.average_delivery_days(orders, RAPIDSHIP, config, after=True)
    delivery_ok = (
        rapidship_days_after is not None
        and swiftship_after is not None
        and 4.0 <= rapidship_days_after <= 5.5
        and rapidship_days_after - swiftship_after >= 1.0
    )
    report.checks.append(
        ValidationCheck(
            "RapidShip delivery time increase after the incident",
            delivery_ok,
            f"rapidship_avg={rapidship_days_after}, swiftship_avg={swiftship_after}",
            {"rapidship_avg_days_after": rapidship_days_after, "swiftship_avg_days_after": swiftship_after},
        )
    )

    late_before = metrics.late_delivery_refund_rate(orders, refunds, config, after=False)
    late_after = metrics.late_delivery_refund_rate(orders, refunds, config, after=True)
    report.checks.append(
        ValidationCheck(
            "Late-delivery refunds increase after the incident",
            late_after > late_before * 3 and late_after > 0.01,
            f"before={late_before:.4f}, after={late_after:.4f}",
            {"before": late_before, "after": late_after},
        )
    )

    overall_before = metrics.refund_rate(orders, refunds, config, after=False)
    overall_after = metrics.refund_rate(orders, refunds, config, after=True)
    relative_change = ((overall_after - overall_before) / overall_before * 100) if overall_before else 0.0
    report.checks.append(
        ValidationCheck(
            "Overall refund rate increases ~20-30% (tolerance 15-60%)",
            15.0 <= relative_change <= 60.0,
            f"before={overall_before:.4f}, after={overall_after:.4f}, relative_change={relative_change:.1f}%",
            {"before": overall_before, "after": overall_after, "relative_change_percent": relative_change},
        )
    )

    ship_before = metrics.shipping_ticket_share(support_tickets, config, after=False)
    ship_after = metrics.shipping_ticket_share(support_tickets, config, after=True)
    ship_relative_change = ((ship_after - ship_before) / ship_before * 100) if ship_before else 0.0
    report.checks.append(
        ValidationCheck(
            "Shipping-related ticket share increases ~40-50% (tolerance 20-80%)",
            20.0 <= ship_relative_change <= 80.0,
            f"before={ship_before:.4f}, after={ship_after:.4f}, relative_change={ship_relative_change:.1f}%",
            {"before": ship_before, "after": ship_after, "relative_change_percent": ship_relative_change},
        )
    )


def _check_realistic_noise(report: ValidationReport, config: GeneratorConfig, orders: list[dict], refunds: list[dict]) -> None:
    late_after = metrics.late_delivery_refund_rate(orders, refunds, config, after=True)
    report.checks.append(
        ValidationCheck(
            "Not every delayed order refunds (late-delivery refund rate < 70%)",
            late_after < 0.70,
            f"late_delivery_refund_rate_after={late_after:.4f}",
            late_after,
        )
    )

    after_incident_order_ids = {o["order_id"] for o in orders if o["order_date"].date() >= config.incident_date}
    non_late_refunds_after = [
        r for r in refunds if r["order_id"] in after_incident_order_ids and r["refund_reason"] != "late_delivery"
    ]
    report.checks.append(
        ValidationCheck(
            "Unrelated refund reasons persist after the incident",
            len(non_late_refunds_after) > 0,
            f"{len(non_late_refunds_after)} non-late-delivery refunds after the incident",
            len(non_late_refunds_after),
        )
    )

    before_incident_delayed = [
        o for o in orders if o["order_date"].date() < config.incident_date and o["is_delayed"]
    ]
    report.checks.append(
        ValidationCheck(
            "Some delayed orders exist before the incident too (SwiftShip variance)",
            len(before_incident_delayed) > 0,
            f"{len(before_incident_delayed)} delayed pre-incident orders",
            len(before_incident_delayed),
        )
    )


def validate_dataset(
    config: GeneratorConfig,
    customers: list[dict],
    products: list[dict],
    orders: list[dict],
    refunds: list[dict],
    support_tickets: list[dict],
) -> ValidationReport:
    report = ValidationReport()
    _check_foreign_keys(report, customers, products, orders, refunds, support_tickets)
    _check_row_counts(report, customers, products, orders, refunds, support_tickets)
    _check_incident_patterns(report, config, orders, refunds, support_tickets)
    _check_realistic_noise(report, config, orders, refunds)
    return report


def assert_dataset_valid(report: ValidationReport) -> None:
    if not report.passed:
        failed = [c for c in report.checks if not c.passed]
        details = "\n".join(f"  - {c.name}: {c.detail}" for c in failed)
        raise ValueError(f"Northstar dataset failed validation ({len(failed)} check(s) failed):\n{details}")
