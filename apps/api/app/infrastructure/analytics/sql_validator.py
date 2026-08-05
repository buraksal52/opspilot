"""AST-based SQL validation (SECURITY.md §9-14, ADR-008, ADR-032).

Runs only on already-resolved, physical-identifier SQL (see `sql_resolver`) —
this is the last, independently-enforced gate before execution, and does not
trust that resolution ran correctly (SECURITY.md's "multiple layers"
principle): it re-derives its own judgment about schema/table/statement
safety directly from the parsed AST.
"""
import sqlglot
from sqlglot import exp

ANALYTICS_SCHEMA = "analytics"

# SECURITY.md §9-14: resource-exhaustion, file-system, and network-adjacent
# functions with no legitimate use in a bounded analytical SELECT.
FORBIDDEN_FUNCTIONS = {
    "pg_sleep",
    "pg_sleep_for",
    "pg_sleep_until",
    "dblink",
    "dblink_connect",
    "dblink_exec",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_stat_file",
    "lo_import",
    "lo_export",
    "copy_from_program",
    "pg_terminate_backend",
    "pg_cancel_backend",
}


class SqlValidationError(Exception):
    """Raised when SQL fails a safety check. The message is safe to feed back
    to the LLM as bounded-retry correction guidance (ANALYTICS_ENGINE.md §28)."""


def _function_name(func: exp.Func) -> str:
    if isinstance(func, exp.Anonymous):
        return func.name.lower()
    return func.sql_name().lower()


def validate_and_bound(sql: str, *, allowed_physical_tables: set[str], max_rows: int) -> str:
    """Validates `sql` (already display->physical resolved) and returns a
    normalized, row-bounded SQL string safe to execute. Raises
    `SqlValidationError` — never silently drops or rewrites away a violation
    other than capping/adding LIMIT (SECURITY.md §14: the server, not the
    LLM, is responsible for bounding results)."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except sqlglot.errors.ParseError as exc:
        raise SqlValidationError(f"Could not parse SQL: {exc}") from exc

    if len(statements) != 1:
        raise SqlValidationError("Only a single SQL statement is allowed (no ';'-stacked statements).")

    tree = statements[0]
    if not isinstance(tree, exp.Select):
        raise SqlValidationError("Only SELECT (or WITH ... SELECT) statements are allowed.")

    cte_names = {cte.alias.lower() for cte in tree.find_all(exp.CTE) if cte.alias}
    allowed_lower = {t.lower() for t in allowed_physical_tables}

    for table in tree.find_all(exp.Table):
        if table.name.lower() in cte_names:
            continue  # a CTE self-reference, not a physical dataset table
        if not isinstance(table.this, exp.Identifier):
            raise SqlValidationError("Table references must be plain identifiers, not function calls.")
        if (table.db or "").lower() != ANALYTICS_SCHEMA:
            raise SqlValidationError(f"Table '{table.name}' must be qualified to the '{ANALYTICS_SCHEMA}' schema.")
        if table.name.lower() not in allowed_lower:
            raise SqlValidationError(f"Table '{table.name}' is not an allowed dataset for this workspace.")

    for func in tree.find_all(exp.Func):
        if _function_name(func) in FORBIDDEN_FUNCTIONS:
            raise SqlValidationError(f"Function '{_function_name(func)}' is not permitted.")

    _enforce_row_limit(tree, max_rows)
    return tree.sql(dialect="postgres")


def _enforce_row_limit(tree: exp.Select, max_rows: int) -> None:
    existing = tree.args.get("limit")
    if existing is None:
        tree.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
        return

    try:
        requested = int(existing.expression.sql())
    except (ValueError, TypeError, AttributeError):
        requested = max_rows + 1  # not a plain integer literal — clamp defensively

    if requested > max_rows:
        tree.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
