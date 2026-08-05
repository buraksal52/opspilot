"""SQL generation (ANALYTICS_ENGINE.md §10, BACKLOG.md 5.3).

Generates SQL written against catalog *display* names only (ANALYTICS_ENGINE.md
§5) — this service never sees or produces physical identifiers; that
resolution happens separately in `infrastructure.analytics.sql_resolver`.
Receives no database credentials (ANALYTICS_ENGINE.md §10).
"""
from app.application.analytics.catalog_service import DatasetCatalog, DatasetCatalogEntry
from app.application.analytics.schemas import AnalysisPlan, SQLProposal
from app.infrastructure.llm.base import LLMProvider


def _render_selected_datasets(catalog: DatasetCatalog, dataset_names: list[str]) -> str:
    """Only the datasets the plan selected (ANALYTICS_ENGINE.md §6 — "avoid
    injecting unnecessary schema context"), not the full workspace catalog."""
    selected: list[DatasetCatalogEntry] = []
    for name in dataset_names:
        entry = catalog.get(name)
        if entry is not None:
            selected.append(entry)

    lines = [f"{e.display_name}\n- columns: {', '.join(c.display_name for c in e.columns)}" for e in selected]
    selected_names = {e.display_name.lower() for e in selected}
    relevant_relationships = [
        rel
        for rel in catalog.relationships
        if rel.from_dataset.lower() in selected_names and rel.to_dataset.lower() in selected_names
    ]
    if relevant_relationships:
        lines.append("relationships:")
        lines.extend(f"- {r.from_dataset}.{r.from_column} -> {r.to_dataset}.{r.to_column}" for r in relevant_relationships)
    return "\n".join(lines)


_BASE_INSTRUCTIONS = (
    "You write a single read-only SQL SELECT statement (a WITH...SELECT common table "
    "expression is also allowed) to answer a business question, using PostgreSQL syntax. "
    "Rules:\n"
    "- Use only the dataset and column display names listed below, exactly as spelled — "
    "never invent a name, never use a name not listed.\n"
    "- Write exactly one statement. Never use a semicolon to combine multiple statements.\n"
    "- Only SELECT is allowed — never INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or any "
    "other data-modifying or administrative statement.\n"
    "- When more than one dataset/table is referenced, qualify every column with its table "
    "alias (e.g. orders.customer_id), since unqualified column names cannot always be resolved.\n"
    "- Do not add a LIMIT clause yourself — the application enforces result limits separately.\n"
    "- Timestamp columns are stored as UTC. Compare a timestamp column to a plain calendar date "
    "using an explicit cast, e.g. order_date::date > '2024-07-11'.\n"
    "- Perform aggregation in SQL (COUNT/SUM/AVG/etc.); do not rely on the caller to aggregate "
    "raw rows.\n"
)


def _build_prompt(
    question: str, plan: AnalysisPlan, catalog: DatasetCatalog, *, previous_sql: str | None, error_feedback: str | None
) -> str:
    schema_context = _render_selected_datasets(catalog, plan.intent.datasets)
    steps = "\n".join(f"- {step}" for step in plan.steps)

    correction = ""
    if previous_sql and error_feedback:
        correction = (
            f"\n\nYour previous attempt was rejected. Previous SQL:\n{previous_sql}\n\n"
            f"Rejection reason: {error_feedback}\n\nProduce a corrected SQL statement."
        )

    return (
        f"{_BASE_INSTRUCTIONS}\n"
        f"Datasets available for this question:\n{schema_context}\n\n"
        f"Business question: {question}\n\n"
        f"Analysis plan:\n{steps}"
        f"{correction}"
    )


class SqlGenerationService:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm = llm_provider

    async def generate_sql(
        self,
        *,
        question: str,
        plan: AnalysisPlan,
        catalog: DatasetCatalog,
        previous_sql: str | None = None,
        error_feedback: str | None = None,
    ) -> SQLProposal:
        prompt = _build_prompt(question, plan, catalog, previous_sql=previous_sql, error_feedback=error_feedback)
        return await self._llm.generate_structured(prompt, SQLProposal)
