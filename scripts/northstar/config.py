"""Generator configuration (BACKLOG.md 2.1).

All parameters live here so the dataset can be regenerated deterministically
and so important thresholds are documented in one place instead of scattered
as magic numbers (CLAUDE.md §15).
"""
from dataclasses import dataclass
from datetime import date

# DATA_MODEL.md §25 / DATASET.md §12: an order counts as delayed once delivery
# takes more than this many days. This threshold feeds both dataset generation
# and the `is_delayed` column, and must not be changed silently.
DELAYED_THRESHOLD_DAYS = 4

SWIFTSHIP = "SwiftShip"
RAPIDSHIP = "RapidShip"


@dataclass(frozen=True)
class GeneratorConfig:
    # DATASET.md §29: fixed seed so the same dataset can always be recreated.
    seed: int = 20240711

    # DATASET.md §3: June 1 -> July 31 dataset period.
    start_date: date = date(2024, 6, 1)
    end_date: date = date(2024, 7, 31)

    # DATASET.md §4: the hidden incident date (SwiftShip -> RapidShip migration).
    incident_date: date = date(2024, 7, 11)

    # DATASET.md §8-16: target dataset sizes.
    customer_count: int = 3000
    product_count: int = 100
    order_count: int = 15000

    # DATASET.md §11: RapidShip share of traffic before/after the incident.
    rapidship_share_before: float = 0.03
    rapidship_share_after: float = 0.68

    # DATASET.md §12: delivery-day distribution parameters (days).
    swiftship_mean_days: float = 2.8
    swiftship_stdev_days: float = 0.8
    rapidship_normal_mean_days: float = 4.0
    rapidship_normal_stdev_days: float = 1.0
    rapidship_severe_mean_days: float = 8.5
    rapidship_severe_stdev_days: float = 1.5
    rapidship_severe_probability: float = 0.15

    # DATASET.md §14: refund probabilities. Tuned so the *aggregate* dataset
    # (BACKLOG.md 2.9 validation) lands within DATASET.md §13's 700-900 refund
    # target and §5's ~20-30% overall refund-rate increase after the incident,
    # while late_delivery refunds still spike sharply for delayed orders.
    baseline_refund_probability: float = 0.05
    late_delivery_refund_base_probability: float = 0.05
    late_delivery_refund_probability_cap: float = 0.65

    # DATASET.md §15-17: support ticket volume and shipping-category boost.
    ticket_count: int = 2000
    shipping_ticket_share_before: float = 0.17
    shipping_ticket_share_relative_increase: float = 0.45


DEFAULT_CONFIG = GeneratorConfig()
