"""Northstar Commerce dataset generator entrypoint.

Usage:
    python -m northstar.generate [--output-dir DIR]

Orchestrates the full pipeline described in DATASET.md / BACKLOG.md Phase 2:
customers -> products -> orders -> derived lifetime metrics -> refunds ->
support tickets -> validation -> CSV/document/ground-truth/eval-question
output. Validation failure aborts the run without writing "accepted" output
(DATASET.md §30).
"""
import argparse
import random
from pathlib import Path
from typing import Any

from northstar.config import DEFAULT_CONFIG, GeneratorConfig
from northstar.customers import apply_customer_lifetime_metrics, generate_customers
from northstar.documents import write_all_documents
from northstar.evaluation_questions import build_evaluation_questions
from northstar.ground_truth import build_ground_truth
from northstar.orders import generate_orders
from northstar.products import generate_products
from northstar.refunds import apply_refund_status_to_orders, generate_refunds
from northstar.support_tickets import generate_support_tickets
from northstar.validate import assert_dataset_valid, validate_dataset
from northstar.writer import write_csv, write_json

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "northstar"


def generate_all(config: GeneratorConfig = DEFAULT_CONFIG) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(config.seed)

    customers = generate_customers(rng, config)
    products = generate_products(rng, config)
    orders = generate_orders(rng, config, customers, products)
    apply_customer_lifetime_metrics(customers, orders)

    refunds = generate_refunds(rng, config, orders)
    apply_refund_status_to_orders(orders, refunds)

    support_tickets = generate_support_tickets(rng, config, customers, orders)

    return {
        "customers": customers,
        "products": products,
        "orders": orders,
        "refunds": refunds,
        "support_tickets": support_tickets,
    }


def write_outputs(config: GeneratorConfig, dataset: dict[str, list[dict]], output_dir: Path) -> None:
    csv_dir = output_dir / "csv"
    write_csv(csv_dir / "customers.csv", dataset["customers"])
    write_csv(csv_dir / "products.csv", dataset["products"])
    write_csv(csv_dir / "orders.csv", dataset["orders"])
    write_csv(csv_dir / "refunds.csv", dataset["refunds"])
    write_csv(csv_dir / "support_tickets.csv", dataset["support_tickets"])

    write_all_documents(output_dir / "documents")

    ground_truth = build_ground_truth(config, dataset["orders"], dataset["refunds"], dataset["support_tickets"])
    write_json(output_dir / "private" / "ground_truth.json", ground_truth)

    questions = build_evaluation_questions(config, dataset["orders"], dataset["refunds"], dataset["support_tickets"])
    write_json(output_dir / "eval" / "evaluation_questions.json", questions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Northstar Commerce demo dataset.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    config = DEFAULT_CONFIG
    dataset = generate_all(config)

    report = validate_dataset(
        config,
        dataset["customers"],
        dataset["products"],
        dataset["orders"],
        dataset["refunds"],
        dataset["support_tickets"],
    )
    write_json(args.output_dir / "private" / "validation_report.json", report.to_dict())

    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name}: {check.detail}")

    assert_dataset_valid(report)

    write_outputs(config, dataset, args.output_dir)

    print(
        f"\nGenerated {len(dataset['customers'])} customers, {len(dataset['products'])} products, "
        f"{len(dataset['orders'])} orders, {len(dataset['refunds'])} refunds, "
        f"{len(dataset['support_tickets'])} support tickets -> {args.output_dir}"
    )


if __name__ == "__main__":
    main()
