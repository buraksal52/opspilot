"""Manual/live analytics evaluation (ANALYTICS_ENGINE.md §30, BACKLOG.md 5.9).

Runs the `analytics`-tagged canonical questions (DATASET.md §33,
`data/northstar/eval/evaluation_questions.json`) through the real
AnalyticsQueryService pipeline — real Gemini calls for planning/SQL
generation/interpretation, real Postgres execution under the read-only role —
and compares the computed result against each question's `expected_value`.

This is deliberately NOT part of `make test-api` (TESTING.md §30/§31): it
makes real, paid Gemini API calls. Unlike `evaluate_retrieval.py`'s
recall/precision/MRR (exact metrics over a fixed candidate set), SQL
generation is not guaranteed to produce byte-identical queries between runs,
so the comparison here is a best-effort heuristic — "does the expected number
appear (rounded) somewhere in the computed result" — reported per-question
for a human to read, not asserted as a pass/fail gate.

Usage (requires `make up`'s dev Postgres reachable, a real GEMINI_API_KEY in
.env, and `make generate-northstar` already run):

    make evaluate-analytics
"""
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from sqlalchemy import text  # noqa: E402

from app.application.analytics.catalog_service import DatasetCatalogService  # noqa: E402
from app.application.analytics.interpretation_service import ResultInterpretationService  # noqa: E402
from app.application.analytics.planning_service import AnalysisPlanningService  # noqa: E402
from app.application.analytics.query_database_tool import AnalyticsQueryResult, AnalyticsQueryService, AnalyticsQueryStatus  # noqa: E402
from app.application.analytics.sql_generation_service import SqlGenerationService  # noqa: E402
from app.application.ingestion.dataset_ingestion_service import DatasetIngestionService  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.domain.data_source import SourceType  # noqa: E402
from app.infrastructure.analytics.query_executor import AnalyticsQueryExecutor  # noqa: E402
from app.infrastructure.auth.password_hasher import PasswordHasher  # noqa: E402
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository  # noqa: E402
from app.infrastructure.database.repositories.dataset_repository import DatasetRepository  # noqa: E402
from app.infrastructure.database.repositories.user_repository import UserRepository  # noqa: E402
from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository  # noqa: E402
from app.infrastructure.database.session import async_session_factory, engine  # noqa: E402
from app.infrastructure.llm.gemini_provider import GeminiLLMProvider  # noqa: E402

CSV_DIR = REPO_ROOT / "data" / "northstar" / "csv"
EVAL_QUESTIONS_PATH = REPO_ROOT / "data" / "northstar" / "eval" / "evaluation_questions.json"
DATASET_FILES = ["customers.csv", "products.csv", "orders.csv", "refunds.csv", "support_tickets.csv"]

_TOLERANCE = 0.01


async def _ingest_all_datasets(session, workspace_id: uuid.UUID) -> list[uuid.UUID]:
    ingestion_service = DatasetIngestionService(session)
    data_source_repo = DataSourceRepository(session)

    dataset_ids = []
    for filename in DATASET_FILES:
        path = CSV_DIR / filename
        if not path.exists():
            raise SystemExit(f"Missing {path} — run `make generate-northstar` first.")
        content = path.read_bytes()
        display_name = path.stem
        data_source = await data_source_repo.create(
            workspace_id=workspace_id,
            name=display_name,
            source_type=SourceType.CSV,
            original_filename=filename,
            mime_type="text/csv",
            file_size_bytes=len(content),
            storage_key=f"eval/{workspace_id}/{uuid.uuid4()}.csv",
        )
        dataset = await ingestion_service.ingest(
            workspace_id=workspace_id, data_source_id=data_source.id, name=display_name, content=content
        )
        dataset_ids.append(dataset.id)
    await session.commit()
    return dataset_ids


def _flatten_numbers(value: Any) -> list[float]:
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, dict):
        numbers = []
        for v in value.values():
            numbers.extend(_flatten_numbers(v))
        return numbers
    return []


def _numbers_match(computed: float, expected: float) -> bool:
    # The LLM may express a rate as a fraction (0.049) or a percentage (4.9)
    # — both are a correct answer to "what was the refund rate", so the
    # comparison is unit-agnostic rather than penalizing a representational
    # choice the SQL-generation prompt never constrains.
    return any(
        abs(candidate - expected) <= _TOLERANCE for candidate in (computed, computed / 100, computed * 100)
    )


def _matches_expected(result: AnalyticsQueryResult, expected_value: Any) -> bool:
    if result.status != AnalyticsQueryStatus.OK or result.result is None:
        return False
    computed_numbers = [v for row in result.result.rows for v in row if isinstance(v, (int, float))]
    expected_numbers = _flatten_numbers(expected_value)
    if not expected_numbers:
        return False
    return all(any(_numbers_match(c, e) for c in computed_numbers) for e in expected_numbers)


async def _evaluate(service: AnalyticsQueryService, questions: list[dict], workspace_id: uuid.UUID) -> dict:
    matched = 0
    print(f"\n{'ID':<14} {'Question':<55} {'Status':<18} {'Match':<6} Expected")
    for question in questions:
        result = await service.query(workspace_id=workspace_id, question=question["question"])
        is_match = _matches_expected(result, question["expected_value"])
        matched += int(is_match)
        computed_preview = result.result.rows[:3] if result.result else result.error
        print(
            f"{question['id']:<14} {question['question'][:53]:<55} {result.status.value:<18} "
            f"{'YES' if is_match else 'no':<6} {question['expected_value']}"
        )
        print(f"    computed: {computed_preview}")
        if result.interpretation:
            print(f"    interpretation: {result.interpretation}")

    total = len(questions)
    print(f"\nMatched {matched}/{total} analytics questions within tolerance {_TOLERANCE}.")
    return {"matched": matched, "total": total}


async def _cleanup(session, workspace_id: uuid.UUID, user_id: uuid.UUID, dataset_ids: list[uuid.UUID]) -> None:
    datasets = DatasetRepository(session)
    for dataset_id in dataset_ids:
        dataset = await datasets.get_by_id(dataset_id)
        if dataset is not None:
            await session.execute(text(f"DROP TABLE IF EXISTS analytics.{dataset.physical_table_name}"))
    await session.execute(text("DELETE FROM app.datasets WHERE workspace_id = :wid"), {"wid": workspace_id})
    await session.execute(text("DELETE FROM app.data_sources WHERE workspace_id = :wid"), {"wid": workspace_id})
    await session.execute(text("DELETE FROM app.workspaces WHERE id = :wid"), {"wid": workspace_id})
    await session.execute(text("DELETE FROM app.users WHERE id = :uid"), {"uid": user_id})
    await session.commit()


async def main() -> None:
    settings = get_settings()
    if settings.gemini_api_key.startswith("changeme"):
        raise SystemExit(
            "GEMINI_API_KEY is not set to a real key (.env still has the placeholder). "
            "This evaluation makes real Gemini API calls and needs one — see .env.example."
        )

    # Some agent-tagged questions also carry the "analytics" tag (DATASET.md
    # §33) but only have `expected_behavior`, not a computable `expected_value`
    # — restrict to questions this script can actually score numerically.
    questions = [
        q for q in json.loads(EVAL_QUESTIONS_PATH.read_text()) if "analytics" in q["tags"] and "expected_value" in q
    ]
    if not questions:
        raise SystemExit(f"No 'analytics'-tagged questions found in {EVAL_QUESTIONS_PATH}.")

    async with async_session_factory() as session:
        user = await UserRepository(session).create(
            email=f"eval-{uuid.uuid4().hex[:8]}@opspilot.local",
            hashed_password=PasswordHasher().hash("evaluation-only-not-a-real-account"),
        )
        workspace = await WorkspaceRepository(session).create(
            name="Analytics Evaluation", slug=f"analytics-eval-{uuid.uuid4().hex[:8]}", owner_id=user.id
        )
        await session.commit()

        dataset_ids: list[uuid.UUID] = []
        try:
            print(f"Ingesting {len(DATASET_FILES)} Northstar datasets into workspace {workspace.id}...")
            dataset_ids = await _ingest_all_datasets(session, workspace.id)

            llm = GeminiLLMProvider(api_key=settings.gemini_api_key, model=settings.llm_model)
            catalog_service = DatasetCatalogService(DatasetRepository(session))
            execution_service = AnalyticsQueryExecutor(
                engine,
                readonly_role=settings.analytics_readonly_role,
                max_rows=settings.analytics_max_result_rows,
                timeout_seconds=settings.analytics_query_timeout_seconds,
            )
            service = AnalyticsQueryService(
                catalog_service,
                AnalysisPlanningService(llm),
                SqlGenerationService(llm),
                execution_service,
                max_generation_attempts=settings.analytics_max_sql_generation_attempts,
                max_result_rows=settings.analytics_max_result_rows,
                interpretation_service=ResultInterpretationService(llm),
            )

            print("Running analytics evaluation (real Gemini + real Postgres execution)...")
            await _evaluate(service, questions, workspace.id)
        finally:
            await _cleanup(session, workspace.id, user.id, dataset_ids)


if __name__ == "__main__":
    asyncio.run(main())
