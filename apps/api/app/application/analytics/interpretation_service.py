"""Natural-language result interpretation (ANALYTICS_ENGINE.md §2/§3/§15,
BACKLOG.md 5.6).

Free-form text (ADR-031) — presentation prose only, generated *after*
deterministic computation. The prompt explicitly forbids introducing any
number not already present in the result (ANALYTICS_ENGINE.md §15: "all
numerical values must derive from query/calculation outputs").
"""
from app.application.analytics.results import QueryResult
from app.application.analytics.schemas import AnalysisPlan
from app.infrastructure.llm.base import LLMProvider

_MAX_PROMPT_ROWS = 50


def _render_result(result: QueryResult) -> str:
    header = ", ".join(result.columns)
    rows = "\n".join(", ".join(str(v) for v in row) for row in result.rows[:_MAX_PROMPT_ROWS])
    truncated_note = "" if result.row_count <= _MAX_PROMPT_ROWS else f"\n(... {result.row_count} rows total)"
    return f"{header}\n{rows}{truncated_note}"


def _build_prompt(question: str, plan: AnalysisPlan, result: QueryResult) -> str:
    return (
        "Explain the following computed analytical result in plain business language, in 1-3 "
        "sentences. Only use numbers that literally appear in the result below — never compute, "
        "round differently, or introduce any number not shown. If the result does not clearly "
        "answer the question, say so honestly instead of guessing.\n\n"
        f"Business question: {question}\n\n"
        f"Analysis steps taken:\n{chr(10).join('- ' + s for s in plan.steps)}\n\n"
        f"Computed result:\n{_render_result(result)}"
    )


class ResultInterpretationService:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm = llm_provider

    async def interpret(self, *, question: str, plan: AnalysisPlan, result: QueryResult) -> str:
        return await self._llm.generate(_build_prompt(question, plan, result))
