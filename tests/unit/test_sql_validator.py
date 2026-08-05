"""SQL validation security tests (TESTING.md §5, SECURITY.md §38)."""
import pytest

from app.infrastructure.analytics.sql_validator import SqlValidationError, validate_and_bound

ALLOWED = {"ds_orders", "ds_customers"}


def test_allows_plain_select_on_an_allowed_table():
    result = validate_and_bound("SELECT * FROM analytics.ds_orders", allowed_physical_tables=ALLOWED, max_rows=500)
    assert "LIMIT 500" in result


def test_allows_with_select_cte():
    sql = "WITH agg AS (SELECT * FROM analytics.ds_orders) SELECT * FROM agg"
    result = validate_and_bound(sql, allowed_physical_tables=ALLOWED, max_rows=500)
    assert "agg" in result


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM analytics.ds_orders",
        "DROP TABLE analytics.ds_orders",
        "UPDATE analytics.ds_orders SET col_1 = 0",
        "TRUNCATE TABLE analytics.ds_orders",
        "ALTER TABLE analytics.ds_orders ADD COLUMN x int",
        "CREATE TABLE analytics.evil (x int)",
        "INSERT INTO analytics.ds_orders VALUES (1)",
        "GRANT SELECT ON analytics.ds_orders TO PUBLIC",
    ],
)
def test_rejects_non_select_statements(sql):
    with pytest.raises(SqlValidationError):
        validate_and_bound(sql, allowed_physical_tables=ALLOWED, max_rows=500)


def test_rejects_stacked_statements():
    with pytest.raises(SqlValidationError, match="single SQL statement"):
        validate_and_bound(
            "SELECT * FROM analytics.ds_orders; DROP TABLE analytics.ds_orders;",
            allowed_physical_tables=ALLOWED,
            max_rows=500,
        )


def test_rejects_table_outside_workspace_allowlist():
    with pytest.raises(SqlValidationError, match="not an allowed dataset"):
        validate_and_bound("SELECT * FROM analytics.ds_other_workspace", allowed_physical_tables=ALLOWED, max_rows=500)


def test_rejects_table_outside_analytics_schema():
    with pytest.raises(SqlValidationError, match="analytics"):
        validate_and_bound("SELECT * FROM app.users", allowed_physical_tables=ALLOWED, max_rows=500)


def test_rejects_unqualified_table_even_if_name_matches():
    with pytest.raises(SqlValidationError, match="must be qualified"):
        validate_and_bound("SELECT * FROM ds_orders", allowed_physical_tables=ALLOWED, max_rows=500)


@pytest.mark.parametrize("sql", ["SELECT pg_sleep(10)", "SELECT dblink('conn', 'select 1')"])
def test_rejects_forbidden_functions(sql):
    with pytest.raises(SqlValidationError, match="not permitted"):
        validate_and_bound(sql, allowed_physical_tables=ALLOWED, max_rows=500)


def test_injects_limit_when_missing():
    result = validate_and_bound("SELECT * FROM analytics.ds_orders", allowed_physical_tables=ALLOWED, max_rows=100)
    assert "LIMIT 100" in result


def test_caps_an_excessive_limit():
    result = validate_and_bound(
        "SELECT * FROM analytics.ds_orders LIMIT 999999999", allowed_physical_tables=ALLOWED, max_rows=100
    )
    assert "LIMIT 100" in result
    assert "999999999" not in result


def test_preserves_a_limit_already_within_bounds():
    result = validate_and_bound(
        "SELECT * FROM analytics.ds_orders LIMIT 10", allowed_physical_tables=ALLOWED, max_rows=500
    )
    assert "LIMIT 10" in result


def test_rejects_table_valued_function_used_as_a_table():
    with pytest.raises(SqlValidationError):
        validate_and_bound(
            "SELECT * FROM generate_series(1, 100000000)", allowed_physical_tables=ALLOWED, max_rows=500
        )


def test_rejects_unparseable_sql():
    with pytest.raises(SqlValidationError):
        validate_and_bound("SELECT FROM WHERE ***", allowed_physical_tables=ALLOWED, max_rows=500)
