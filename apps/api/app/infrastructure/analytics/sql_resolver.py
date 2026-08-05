"""Display-name -> physical-identifier SQL resolution (ANALYTICS_ENGINE.md §5,
ADR-017, ADR-032).

The LLM is shown only catalog display names and never told about physical
identifiers (ANALYTICS_ENGINE.md §5). This module rewrites its SQL so every
dataset/column reference becomes the real `analytics.<physical_table_name>` /
`<physical_name>` identifier — using an AST rewrite (sqlglot), never string
substitution, since a display name could otherwise appear inside a string
literal or as a substring of an unrelated identifier.

Scope is intentionally bounded to the patterns the SQL-generation prompt
actually offers the LLM: real dataset tables, joins between them, and CTEs
(`WITH ... SELECT`). Derived subqueries in FROM are not a supported nesting
mechanism (the prompt never offers them) and are treated the same as an
unknown table if they appear — a resolution failure that feeds back into the
bounded-retry loop (ANALYTICS_ENGINE.md §28), not a silent misresolution.
"""
import sqlglot
from sqlglot import exp

from app.application.analytics.catalog_service import DatasetCatalog, DatasetCatalogEntry

ANALYTICS_SCHEMA = "analytics"


class SqlResolutionError(Exception):
    """Raised when generated SQL references a table/column that cannot be
    mapped to the workspace's catalog, or combines multiple statements. The
    message is safe to feed back to the LLM as correction guidance."""


def _output_aliases(select: exp.Select) -> set[str]:
    aliases: set[str] = set()
    for item in select.expressions:
        alias = item.args.get("alias") if hasattr(item, "args") else None
        if alias is not None:
            aliases.add(alias.name.lower() if hasattr(alias, "name") else str(alias).lower())
    return aliases


def _local_table_nodes(select: exp.Select) -> list[exp.Table]:
    tables: list[exp.Table] = []
    from_ = select.args.get("from_")
    if from_ is not None:
        tables.extend(from_.find_all(exp.Table))
    for join in select.args.get("joins") or []:
        tables.extend(join.find_all(exp.Table))
    return tables


def resolve_identifiers(sql: str, catalog: DatasetCatalog) -> str:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise SqlResolutionError(f"Could not parse the generated SQL: {exc}") from exc

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise SqlResolutionError("Only a single SQL statement is allowed — remove any extra ';'-separated statements.")

    tree = statements[0]
    cte_names = {cte.alias.lower() for cte in tree.find_all(exp.CTE) if cte.alias}

    # scope_alias_maps: id(enclosing Select) -> {alias-or-name (lower): entry or None (CTE)}
    scope_alias_maps: dict[int, dict[str, DatasetCatalogEntry | None]] = {}

    for select in tree.find_all(exp.Select):
        alias_map: dict[str, DatasetCatalogEntry | None] = {}
        for table in _local_table_nodes(select):
            alias_key = (table.alias or table.name).lower()
            name_lower = table.name.lower()

            if name_lower in cte_names:
                alias_map[alias_key] = None
                continue

            entry = catalog.get(table.name)
            if entry is None:
                raise SqlResolutionError(
                    f"Unknown dataset '{table.name}' — use only the datasets listed in the catalog."
                )
            alias_map[alias_key] = entry
            had_explicit_alias = bool(table.alias)
            original_name = table.name
            table.set("this", exp.to_identifier(entry.physical_table_name))
            table.set("db", exp.to_identifier(ANALYTICS_SCHEMA))
            if not had_explicit_alias:
                # Column qualifiers elsewhere in the query (e.g. `orders.col_1`)
                # still say the *original* display name — sqlglot does not
                # retroactively update them when a Table node is renamed. Add
                # an alias back to the original name so those qualifiers keep
                # resolving to this table instead of becoming a dangling
                # reference to a relation that no longer exists.
                table.set("alias", exp.TableAlias(this=exp.to_identifier(original_name)))

        scope_alias_maps[id(select)] = alias_map

    for column in tree.find_all(exp.Column):
        enclosing_select = column.find_ancestor(exp.Select)
        if enclosing_select is None:
            continue
        alias_map = scope_alias_maps.get(id(enclosing_select), {})

        if column.table:
            key = column.table.lower()
            if key not in alias_map:
                raise SqlResolutionError(f"Unknown table qualifier '{column.table}' on column '{column.name}'.")
            entry = alias_map[key]
            if entry is None:
                continue  # qualifies a CTE, not a physical dataset — leave as-is
            col_entry = entry.column(column.name)
            if col_entry is None:
                raise SqlResolutionError(f"Unknown column '{column.name}' on dataset '{entry.display_name}'.")
            column.set("this", exp.to_identifier(col_entry.physical_name))
            continue

        dataset_entries = [e for e in alias_map.values() if e is not None]
        if not dataset_entries:
            continue  # only CTEs/no tables in scope — column belongs to a CTE's own output

        if column.name.lower() in _output_aliases(enclosing_select):
            continue  # refers to this SELECT's own output alias (e.g. GROUP BY/ORDER BY by alias)

        matches = [e for e in dataset_entries if e.column(column.name) is not None]
        if len(matches) == 0:
            raise SqlResolutionError(f"Unknown column '{column.name}' — it matches no available dataset.")
        if len(matches) > 1:
            raise SqlResolutionError(f"Ambiguous column '{column.name}' — qualify it with a table alias.")

        col_entry = matches[0].column(column.name)
        column.set("this", exp.to_identifier(col_entry.physical_name))

    return tree.sql(dialect="postgres")
