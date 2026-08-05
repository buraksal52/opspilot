"""Known Northstar dataset relationships (ANALYTICS_ENGINE.md §7, DATASET.md
§31) — declared once, resolved dynamically per request against whatever
datasets actually exist in the requesting workspace.

This is intentionally a small, static, documented list, not a general
semantic-relationship platform (DATA_MODEL.md §11: "avoid prematurely
building a full semantic-layer platform... may be stored inside dataset
metadata if sufficient"). Only the relationships DATASET.md/ANALYTICS_ENGINE.md
explicitly document are declared here.
"""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RelationshipHint:
    from_dataset: str
    from_column: str
    to_dataset: str
    to_column: str


KNOWN_RELATIONSHIPS: list[RelationshipHint] = [
    RelationshipHint("orders", "customer_id", "customers", "customer_id"),
    RelationshipHint("orders", "product_id", "products", "product_id"),
    RelationshipHint("refunds", "order_id", "orders", "order_id"),
    RelationshipHint("support_tickets", "order_id", "orders", "order_id"),
]
