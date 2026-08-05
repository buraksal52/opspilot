"""`query_database` — the single agent-facing analytics tool facade
(AGENT_SYSTEM.md §12, BACKLOG.md 5.6).

Orchestrates the full ANALYTICS_ENGINE.md §2 workflow: catalog -> planning ->
SQL generation -> identifier resolution -> validation (bounded retry,
ANALYTICS_ENGINE.md §28) -> read-only execution -> evidence-shaped structured
result. No agent exists yet (Phase 6) to call this — it is directly callable
and tested on its own, the same pattern Phase 4 established for
`EmbeddingGenerationService`/`VectorSearchService`.
"""
import logging
import uuid
from dataclasses import dataclass
from enum import StrEnum

from app.application.analytics.catalog_service import DatasetCatalogService
from app.application.analytics.interpretation_service import ResultInterpretationService
from app.application.analytics.planning_service import AnalysisPlanningService, NoDatasetsAvailableError
from app.application.analytics.results import AnalyticsEvidence, QueryResult
from app.application.analytics.schemas import AnalysisPlan
from app.application.analytics.sql_generation_service import SqlGenerationService
from app.infrastructure.analytics.query_executor import AnalyticsExecutionError, AnalyticsQueryExecutor
from app.infrastructure.analytics.sql_resolver import SqlResolutionError, resolve_identifiers
from app.infrastructure.analytics.sql_validator import SqlValidationError, validate_and_bound

logger = logging.getLogger(__name__)


class AnalyticsQueryStatus(StrEnum):
    OK = "OK"
    # ANALYTICS_ENGINE.md §29 failure modes, returned structurally rather
    # than raised, so a caller (eventually the Phase 6 agent) can handle
    # "insufficient data" honestly (ANALYTICS_ENGINE.md §19) instead of a
    # generic exception.
    NO_DATASETS = "NO_DATASETS"
    NO_RELEVANT_DATASET = "NO_RELEVANT_DATASET"
    GENERATION_FAILED = "GENERATION_FAILED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


@dataclass(frozen=True, slots=True)
class AnalyticsQueryResult:
    status: AnalyticsQueryStatus
    plan: AnalysisPlan | None
    result: QueryResult | None
    evidence: AnalyticsEvidence | None
    interpretation: str | None
    error: str | None


class AnalyticsQueryService:
    def __init__(
        self,
        catalog_service: DatasetCatalogService,
        planning_service: AnalysisPlanningService,
        sql_generation_service: SqlGenerationService,
        execution_service: AnalyticsQueryExecutor,
        *,
        max_generation_attempts: int,
        max_result_rows: int,
        interpretation_service: ResultInterpretationService | None = None,
    ) -> None:
        self._catalog = catalog_service
        self._planning = planning_service
        self._sql_generation = sql_generation_service
        self._execution = execution_service
        self._max_attempts = max_generation_attempts
        self._max_rows = max_result_rows
        self._interpretation = interpretation_service

    async def query(self, *, workspace_id: uuid.UUID, question: str) -> AnalyticsQueryResult:
        catalog = await self._catalog.get_catalog(workspace_id)

        try:
            plan = await self._planning.create_plan(question=question, catalog=catalog)
        except NoDatasetsAvailableError as exc:
            return _empty_result(AnalyticsQueryStatus.NO_DATASETS, error=str(exc))

        selected_names = [name for name in plan.intent.datasets if catalog.get(name) is not None]
        if not selected_names:
            return _empty_result(AnalyticsQueryStatus.NO_RELEVANT_DATASET, plan=plan)

        dataset_ids = [catalog.get(name).dataset_id for name in selected_names]
        allowed_tables = {entry.physical_table_name for entry in catalog.entries}

        bounded_sql, generation_error = await self._generate_valid_sql(question, plan, catalog)
        if bounded_sql is None:
            return _empty_result(AnalyticsQueryStatus.GENERATION_FAILED, plan=plan, error=generation_error)

        try:
            query_result = await self._execution.execute(bounded_sql)
        except AnalyticsExecutionError as exc:
            logger.warning("Analytics query execution failed: %s", exc)
            return _empty_result(AnalyticsQueryStatus.EXECUTION_FAILED, plan=plan, error=str(exc))

        evidence = AnalyticsEvidence(dataset_ids=dataset_ids, sql=bounded_sql, result=query_result)

        interpretation = None
        if self._interpretation is not None:
            interpretation = await self._interpretation.interpret(question=question, plan=plan, result=query_result)

        return AnalyticsQueryResult(
            status=AnalyticsQueryStatus.OK,
            plan=plan,
            result=query_result,
            evidence=evidence,
            interpretation=interpretation,
            error=None,
        )

    async def _generate_valid_sql(self, question: str, plan: AnalysisPlan, catalog) -> tuple[str | None, str | None]:
        allowed_tables = {entry.physical_table_name for entry in catalog.entries}
        previous_sql: str | None = None
        error_feedback: str | None = None
        last_error: str | None = None

        for attempt in range(self._max_attempts):
            proposal = await self._sql_generation.generate_sql(
                question=question, plan=plan, catalog=catalog, previous_sql=previous_sql, error_feedback=error_feedback
            )
            try:
                physical_sql = resolve_identifiers(proposal.sql, catalog)
                bounded_sql = validate_and_bound(physical_sql, allowed_physical_tables=allowed_tables, max_rows=self._max_rows)
                return bounded_sql, None
            except (SqlResolutionError, SqlValidationError) as exc:
                last_error = str(exc)
                logger.info("SQL generation attempt %d/%d rejected: %s", attempt + 1, self._max_attempts, last_error)
                previous_sql = proposal.sql
                error_feedback = last_error

        return None, last_error


def _empty_result(
    status: AnalyticsQueryStatus, *, plan: AnalysisPlan | None = None, error: str | None = None
) -> AnalyticsQueryResult:
    return AnalyticsQueryResult(status=status, plan=plan, result=None, evidence=None, interpretation=None, error=error)
