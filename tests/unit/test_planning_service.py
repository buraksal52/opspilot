import uuid

import pytest

from app.application.analytics.catalog_service import ColumnCatalogEntry, DatasetCatalog, DatasetCatalogEntry
from app.application.analytics.planning_service import AnalysisPlanningService, NoDatasetsAvailableError
from app.application.analytics.schemas import AnalysisPlan, AnalyticalIntent
from app.infrastructure.llm.fake_provider import FakeLLMProvider


def _catalog(entries: list[DatasetCatalogEntry]) -> DatasetCatalog:
    return DatasetCatalog(entries=entries, relationships=[])


def _orders_entry() -> DatasetCatalogEntry:
    return DatasetCatalogEntry(
        dataset_id=uuid.uuid4(),
        display_name="orders",
        physical_table_name="ds_abc",
        row_count=100,
        columns=[ColumnCatalogEntry("order_id", "col_1", "string", False)],
    )


async def test_raises_when_workspace_has_no_datasets():
    service = AnalysisPlanningService(FakeLLMProvider())
    with pytest.raises(NoDatasetsAvailableError):
        await service.create_plan(question="Why did refunds increase?", catalog=_catalog([]))


async def test_returns_the_llm_structured_plan():
    llm = FakeLLMProvider()
    plan = AnalysisPlan(
        intent=AnalyticalIntent(question_type="trend", metrics=["refund_rate"], dimensions=["period"], datasets=["orders"]),
        steps=["Count refunds before July 11.", "Count refunds after July 11."],
    )
    llm.queue_structured(plan)

    result = await AnalysisPlanningService(llm).create_plan(
        question="Why did refunds increase?", catalog=_catalog([_orders_entry()])
    )

    assert result == plan
    assert len(llm.structured_calls) == 1
    prompt, response_model = llm.structured_calls[0]
    assert response_model is AnalysisPlan
    assert "orders" in prompt
    assert "ds_abc" not in prompt  # physical identifier must never reach the prompt
