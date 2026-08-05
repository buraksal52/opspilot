import uuid

import pytest

from app.application.analytics.catalog_service import ColumnCatalogEntry, DatasetCatalog, DatasetCatalogEntry
from app.application.analytics.known_relationships import RelationshipHint
from app.infrastructure.analytics.sql_resolver import SqlResolutionError, resolve_identifiers


def _entry(name: str, physical_table: str, columns: list[tuple[str, str]]) -> DatasetCatalogEntry:
    return DatasetCatalogEntry(
        dataset_id=uuid.uuid4(),
        display_name=name,
        physical_table_name=physical_table,
        row_count=10,
        columns=[ColumnCatalogEntry(display, physical, "string", False) for display, physical in columns],
    )


ORDERS = _entry("orders", "ds_orders", [("order_id", "col_1"), ("customer_id", "col_2"), ("order_date", "col_3")])
CUSTOMERS = _entry("customers", "ds_customers", [("customer_id", "col_1"), ("customer_segment", "col_2")])
CATALOG = DatasetCatalog(
    entries=[ORDERS, CUSTOMERS], relationships=[RelationshipHint("orders", "customer_id", "customers", "customer_id")]
)


def test_resolves_simple_select_to_physical_identifiers():
    resolved = resolve_identifiers("SELECT order_id, customer_id FROM orders", CATALOG)
    assert "analytics.ds_orders" in resolved
    assert "col_1" in resolved and "col_2" in resolved


def test_unaliased_table_gets_an_alias_back_so_column_qualifiers_still_resolve():
    # "orders" has no explicit alias in the source SQL, but a later clause
    # still qualifies columns with the original display name — this must not
    # become a dangling reference once the table is renamed to its physical
    # identifier (a real failure caught by a live end-to-end run).
    resolved = resolve_identifiers("SELECT orders.order_id FROM orders WHERE orders.customer_id = 'X'", CATALOG)
    assert "analytics.ds_orders AS orders" in resolved
    assert "orders.col_1" in resolved
    assert "orders.col_2" in resolved


def test_resolves_qualified_columns_across_a_join():
    sql = (
        "SELECT o.order_id, c.customer_segment FROM orders o "
        "JOIN customers c ON o.customer_id = c.customer_id"
    )
    resolved = resolve_identifiers(sql, CATALOG)
    assert "analytics.ds_orders" in resolved
    assert "analytics.ds_customers" in resolved
    assert "col_2" in resolved  # customer_segment on customers


def test_resolves_columns_inside_a_cte_and_leaves_cte_alias_untouched():
    sql = (
        "WITH agg AS (SELECT customer_id, COUNT(*) AS n FROM orders GROUP BY customer_id) "
        "SELECT agg.customer_id, agg.n FROM agg WHERE agg.n > 1"
    )
    resolved = resolve_identifiers(sql, CATALOG)
    assert "analytics.ds_orders" in resolved
    assert "col_2" in resolved  # customer_id inside the CTE body
    assert "agg.n" in resolved or "AGG.N" in resolved.upper()  # CTE-qualified reference left as-is


def test_group_by_output_alias_is_not_treated_as_an_unknown_column():
    sql = "SELECT customer_id AS cid, COUNT(*) AS n FROM orders GROUP BY cid"
    resolved = resolve_identifiers(sql, CATALOG)
    assert "cid" in resolved
    assert "col_2" in resolved


def test_unknown_table_raises():
    with pytest.raises(SqlResolutionError, match="Unknown dataset"):
        resolve_identifiers("SELECT * FROM refunds", CATALOG)


def test_unknown_column_raises():
    with pytest.raises(SqlResolutionError, match="Unknown column"):
        resolve_identifiers("SELECT nonexistent_column FROM orders", CATALOG)


def test_ambiguous_unqualified_column_raises():
    sql = "SELECT customer_id FROM orders, customers"
    with pytest.raises(SqlResolutionError, match="Ambiguous"):
        resolve_identifiers(sql, CATALOG)


def test_stacked_statements_rejected():
    with pytest.raises(SqlResolutionError, match="single SQL statement"):
        resolve_identifiers("SELECT * FROM orders; DROP TABLE orders;", CATALOG)


def test_unparseable_sql_raises():
    with pytest.raises(SqlResolutionError):
        resolve_identifiers("SELECT FROM WHERE ***", CATALOG)
