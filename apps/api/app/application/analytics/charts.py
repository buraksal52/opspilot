"""Chart specification generation (ANALYTICS_ENGINE.md §25, DATA_MODEL.md §23,
BACKLOG.md 5.8).

A pure, deterministic transform from an already-executed, validated
`QueryResult` — never independently invents data (AGENT_SYSTEM.md §15). No
image generation; the frontend renders structured chart data
(ANALYTICS_ENGINE.md §25). Actual frontend rendering is Phase 7 scope (no
Investigation Workspace page exists yet to host a chart) — this module
produces the spec/data only.
"""
from dataclasses import dataclass

from app.application.analytics.results import QueryResult


class ChartGenerationError(Exception):
    """Raised when the requested columns don't exist in the query result."""


@dataclass(frozen=True, slots=True)
class ChartSeries:
    name: str
    values: list


@dataclass(frozen=True, slots=True)
class ChartSpec:
    type: str
    title: str
    x: list
    series: list[ChartSeries]


def build_chart_from_result(
    result: QueryResult, *, chart_type: str, title: str, x_column: str, series_columns: list[str]
) -> ChartSpec:
    if x_column not in result.columns:
        raise ChartGenerationError(f"x_column '{x_column}' is not in the query result columns.")
    missing = [c for c in series_columns if c not in result.columns]
    if missing:
        raise ChartGenerationError(f"series_columns not in the query result: {missing}")

    x_index = result.columns.index(x_column)
    x_values = [row[x_index] for row in result.rows]

    series = []
    for column in series_columns:
        index = result.columns.index(column)
        series.append(ChartSeries(name=column, values=[row[index] for row in result.rows]))

    return ChartSpec(type=chart_type, title=title, x=x_values, series=series)
