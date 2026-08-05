"""Analysis planning (ANALYTICS_ENGINE.md §8-9, BACKLOG.md 5.2).

Translates a natural-language business question into a structured
AnalyticalIntent + brief step-by-step AnalysisPlan, using only the catalog's
display names (ANALYTICS_ENGINE.md §5-6) — never physical identifiers.
"""
from app.application.analytics.catalog_service import DatasetCatalog
from app.application.analytics.schemas import AnalysisPlan
from app.infrastructure.llm.base import LLMProvider


class NoDatasetsAvailableError(Exception):
    """Raised when the workspace has no READY datasets at all — a distinct,
    cheaper-to-detect case than "the LLM found no dataset relevant to this
    specific question" (ANALYTICS_ENGINE.md §29), so no LLM call is wasted."""


def _build_prompt(question: str, catalog: DatasetCatalog) -> str:
    return (
        "You are planning a structured data analysis for a business-investigation system. "
        "You may only reference dataset and column names exactly as listed below — never invent "
        "a dataset or column name, and never use any name not shown here.\n\n"
        f"Available datasets:\n{catalog.render()}\n\n"
        f"Business question: {question}\n\n"
        "Produce a question_type, the metrics and dimensions involved, the datasets needed "
        "(display names only, from the list above), and a short ordered list of concrete "
        "analytical steps (e.g. 'Count refunds before July 11.'). If no listed dataset is "
        "relevant to the question, return an empty datasets list."
    )


class AnalysisPlanningService:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm = llm_provider

    async def create_plan(self, *, question: str, catalog: DatasetCatalog) -> AnalysisPlan:
        if not catalog.entries:
            raise NoDatasetsAvailableError("The workspace has no ready datasets to analyze.")

        prompt = _build_prompt(question, catalog)
        return await self._llm.generate_structured(prompt, AnalysisPlan)
