"""AnalyticsQueryService end-to-end over a real Postgres dataset table, using
FakeLLMProvider so no live Gemini calls happen here (TESTING.md §30) — the
live-model path is exercised separately by `scripts/evaluate_analytics.py`.
"""
import uuid

import pytest

from app.application.analytics.catalog_service import DatasetCatalogService
from app.application.analytics.interpretation_service import ResultInterpretationService
from app.application.analytics.planning_service import AnalysisPlanningService
from app.application.analytics.query_database_tool import AnalyticsQueryService, AnalyticsQueryStatus
from app.application.analytics.schemas import AnalysisPlan, AnalyticalIntent, SQLProposal
from app.application.analytics.sql_generation_service import SqlGenerationService
from app.application.ingestion.dataset_ingestion_service import DatasetIngestionService
from app.core.config import get_settings
from app.infrastructure.analytics.query_executor import AnalyticsExecutionError, AnalyticsQueryExecutor
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository
from app.infrastructure.database.repositories.dataset_repository import DatasetRepository
from app.infrastructure.database.session import engine
from app.infrastructure.llm.fake_provider import FakeLLMProvider
from app.domain.data_source import SourceType

pytestmark = pytest.mark.usefixtures("_migrated_database")

ORDERS_CSV = b"order_id,total_amount\nORD-1,10.5\nORD-2,20\nORD-3,5\n"


@pytest.fixture
def executor():
    settings = get_settings()
    return AnalyticsQueryExecutor(
        engine, readonly_role=settings.analytics_readonly_role, max_rows=500, timeout_seconds=5.0
    )


@pytest.fixture
async def seeded_orders_dataset(db_session, seeded_workspace):
    data_source = await DataSourceRepository(db_session).create(
        workspace_id=seeded_workspace.id,
        name="orders.csv",
        source_type=SourceType.CSV,
        original_filename="orders.csv",
        mime_type="text/csv",
        file_size_bytes=len(ORDERS_CSV),
        storage_key=f"{seeded_workspace.id}/{uuid.uuid4()}.csv",
    )
    dataset = await DatasetIngestionService(db_session).ingest(
        workspace_id=seeded_workspace.id, data_source_id=data_source.id, name="orders", content=ORDERS_CSV
    )
    await db_session.commit()
    return dataset


async def test_full_pipeline_returns_ok_with_evidence(db_session, seeded_workspace, seeded_orders_dataset, executor):
    llm = FakeLLMProvider()
    llm.queue_structured(
        AnalysisPlan(
            intent=AnalyticalIntent(question_type="aggregation", metrics=["order_count"], dimensions=[], datasets=["orders"]),
            steps=["Count all orders."],
        )
    )
    llm.queue_structured(SQLProposal(sql="SELECT COUNT(*) AS order_count FROM orders"))

    service = AnalyticsQueryService(
        DatasetCatalogService(DatasetRepository(db_session)),
        AnalysisPlanningService(llm),
        SqlGenerationService(llm),
        executor,
        max_generation_attempts=2,
        max_result_rows=500,
    )

    result = await service.query(workspace_id=seeded_workspace.id, question="How many orders are there?")

    assert result.status == AnalyticsQueryStatus.OK
    assert result.result.rows == [[3]]
    assert result.evidence.dataset_ids == [seeded_orders_dataset.id]
    assert "analytics." in result.evidence.sql
    assert result.interpretation is None  # no interpretation service configured


async def test_bounded_retry_recovers_from_an_invalid_first_attempt(db_session, seeded_workspace, seeded_orders_dataset, executor):
    llm = FakeLLMProvider()
    llm.queue_structured(
        AnalysisPlan(
            intent=AnalyticalIntent(question_type="aggregation", metrics=[], dimensions=[], datasets=["orders"]),
            steps=["Count all orders."],
        )
    )
    llm.queue_structured(SQLProposal(sql="SELECT * FROM refunds"))  # unknown dataset -> resolution failure
    llm.queue_structured(SQLProposal(sql="SELECT COUNT(*) AS n FROM orders"))  # corrected

    service = AnalyticsQueryService(
        DatasetCatalogService(DatasetRepository(db_session)),
        AnalysisPlanningService(llm),
        SqlGenerationService(llm),
        executor,
        max_generation_attempts=2,
        max_result_rows=500,
    )

    result = await service.query(workspace_id=seeded_workspace.id, question="How many orders?")

    assert result.status == AnalyticsQueryStatus.OK
    assert result.result.rows == [[3]]


async def test_generation_failed_when_all_attempts_are_invalid(db_session, seeded_workspace, seeded_orders_dataset, executor):
    llm = FakeLLMProvider()
    llm.queue_structured(
        AnalysisPlan(
            intent=AnalyticalIntent(question_type="aggregation", metrics=[], dimensions=[], datasets=["orders"]),
            steps=["Count all orders."],
        )
    )
    llm.queue_structured(SQLProposal(sql="SELECT * FROM refunds"))

    service = AnalyticsQueryService(
        DatasetCatalogService(DatasetRepository(db_session)),
        AnalysisPlanningService(llm),
        SqlGenerationService(llm),
        executor,
        max_generation_attempts=1,
        max_result_rows=500,
    )

    result = await service.query(workspace_id=seeded_workspace.id, question="How many orders?")

    assert result.status == AnalyticsQueryStatus.GENERATION_FAILED
    assert result.error is not None


async def test_no_datasets_status_when_workspace_is_empty(db_session, seeded_workspace, executor):
    llm = FakeLLMProvider()
    service = AnalyticsQueryService(
        DatasetCatalogService(DatasetRepository(db_session)),
        AnalysisPlanningService(llm),
        SqlGenerationService(llm),
        executor,
        max_generation_attempts=2,
        max_result_rows=500,
    )

    result = await service.query(workspace_id=seeded_workspace.id, question="Anything?")

    assert result.status == AnalyticsQueryStatus.NO_DATASETS


async def test_no_relevant_dataset_when_the_plan_selects_nothing(db_session, seeded_workspace, seeded_orders_dataset, executor):
    llm = FakeLLMProvider()
    llm.queue_structured(
        AnalysisPlan(
            intent=AnalyticalIntent(question_type="lookup", metrics=[], dimensions=[], datasets=[]), steps=[]
        )
    )

    service = AnalyticsQueryService(
        DatasetCatalogService(DatasetRepository(db_session)),
        AnalysisPlanningService(llm),
        SqlGenerationService(llm),
        executor,
        max_generation_attempts=2,
        max_result_rows=500,
    )

    result = await service.query(workspace_id=seeded_workspace.id, question="What's the weather?")

    assert result.status == AnalyticsQueryStatus.NO_RELEVANT_DATASET


class _FailingExecutor:
    async def execute(self, sql: str):
        raise AnalyticsExecutionError("boom")


async def test_execution_failed_status_when_the_executor_raises(db_session, seeded_workspace, seeded_orders_dataset):
    llm = FakeLLMProvider()
    llm.queue_structured(
        AnalysisPlan(
            intent=AnalyticalIntent(question_type="aggregation", metrics=[], dimensions=[], datasets=["orders"]),
            steps=["Count all orders."],
        )
    )
    llm.queue_structured(SQLProposal(sql="SELECT COUNT(*) FROM orders"))

    service = AnalyticsQueryService(
        DatasetCatalogService(DatasetRepository(db_session)),
        AnalysisPlanningService(llm),
        SqlGenerationService(llm),
        _FailingExecutor(),
        max_generation_attempts=2,
        max_result_rows=500,
    )

    result = await service.query(workspace_id=seeded_workspace.id, question="How many orders?")

    assert result.status == AnalyticsQueryStatus.EXECUTION_FAILED
    assert result.error == "boom"


async def test_interpretation_is_included_when_configured(db_session, seeded_workspace, seeded_orders_dataset, executor):
    llm = FakeLLMProvider()
    llm.queue_structured(
        AnalysisPlan(
            intent=AnalyticalIntent(question_type="aggregation", metrics=[], dimensions=[], datasets=["orders"]),
            steps=["Count all orders."],
        )
    )
    llm.queue_structured(SQLProposal(sql="SELECT COUNT(*) FROM orders"))
    llm.queue_text("There are 3 orders.")

    service = AnalyticsQueryService(
        DatasetCatalogService(DatasetRepository(db_session)),
        AnalysisPlanningService(llm),
        SqlGenerationService(llm),
        executor,
        max_generation_attempts=2,
        max_result_rows=500,
        interpretation_service=ResultInterpretationService(llm),
    )

    result = await service.query(workspace_id=seeded_workspace.id, question="How many orders?")

    assert result.interpretation == "There are 3 orders."


async def test_cross_workspace_physical_table_is_rejected_even_though_it_really_exists(
    db_session, seeded_workspace, seeded_orders_dataset, executor
):
    """ADR-017/SECURITY.md §13 — two workspaces each with their own 'orders'
    dataset (same display name, different physical tables). Workspace A's
    allowlist must never include workspace B's physical table, even though it
    genuinely exists in the same `analytics` schema. This directly covers
    BACKLOG.md 5.4's "query referencing another workspace's physical table
    must be rejected" requirement."""
    from app.infrastructure.analytics.sql_validator import SqlValidationError, validate_and_bound
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.database.repositories.user_repository import UserRepository
    from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository

    other_user = await UserRepository(db_session).create(
        email=f"other-{uuid.uuid4().hex[:8]}@example.com", hashed_password=PasswordHasher().hash("irrelevant")
    )
    other_workspace = await WorkspaceRepository(db_session).create(
        name="Other Workspace", slug=f"other-{uuid.uuid4().hex[:8]}", owner_id=other_user.id
    )
    other_data_source = await DataSourceRepository(db_session).create(
        workspace_id=other_workspace.id,
        name="orders.csv",
        source_type=SourceType.CSV,
        original_filename="orders.csv",
        mime_type="text/csv",
        file_size_bytes=len(ORDERS_CSV),
        storage_key=f"{other_workspace.id}/{uuid.uuid4()}.csv",
    )
    other_dataset = await DatasetIngestionService(db_session).ingest(
        workspace_id=other_workspace.id, data_source_id=other_data_source.id, name="orders", content=ORDERS_CSV
    )
    await db_session.commit()

    catalog_a = await DatasetCatalogService(DatasetRepository(db_session)).get_catalog(seeded_workspace.id)
    workspace_a_allowlist = {entry.physical_table_name for entry in catalog_a.entries}

    assert seeded_orders_dataset.physical_table_name in workspace_a_allowlist
    assert other_dataset.physical_table_name not in workspace_a_allowlist

    with pytest.raises(SqlValidationError, match="not an allowed dataset"):
        validate_and_bound(
            f"SELECT * FROM analytics.{other_dataset.physical_table_name}",
            allowed_physical_tables=workspace_a_allowlist,
            max_rows=500,
        )
