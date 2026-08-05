"""Structured AI-output schemas for the analytics engine (ADR-011,
ANALYTICS_ENGINE.md §8-9). Whenever AI output affects program logic (which
datasets to use, what SQL to run), it is validated against one of these
Pydantic models rather than parsed from unconstrained prose.
"""
from pydantic import BaseModel, Field


class AnalyticalIntent(BaseModel):
    """ANALYTICS_ENGINE.md §8 — structured representation of what the
    question is asking for, before any SQL exists."""

    question_type: str = Field(description="e.g. 'comparison', 'trend', 'ranking', 'aggregation', 'lookup'.")
    metrics: list[str] = Field(default_factory=list, description="Business metrics the question is about.")
    dimensions: list[str] = Field(default_factory=list, description="Dimensions to group/compare by, e.g. 'period'.")
    datasets: list[str] = Field(description="Display names of datasets relevant to answering the question.")


class AnalysisPlan(BaseModel):
    """ANALYTICS_ENGINE.md §9 — a brief structured plan produced before SQL
    generation, for inspectability. `steps` are short, human-readable."""

    intent: AnalyticalIntent
    steps: list[str] = Field(description="Ordered, concrete analytical steps, e.g. 'Count refunds before July 11.'")


class SQLProposal(BaseModel):
    """ANALYTICS_ENGINE.md §10 — SQL written against catalog display names
    only (ANALYTICS_ENGINE.md §5); never executed as-is, always passed
    through identifier resolution and validation first."""

    sql: str
