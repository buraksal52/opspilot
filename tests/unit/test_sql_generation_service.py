import uuid

from app.application.analytics.catalog_service import ColumnCatalogEntry, DatasetCatalog, DatasetCatalogEntry
from app.application.analytics.known_relationships import RelationshipHint
from app.application.analytics.schemas import AnalysisPlan, AnalyticalIntent, SQLProposal
from app.application.analytics.sql_generation_service import SqlGenerationService
from app.infrastructure.llm.fake_provider import FakeLLMProvider


def _entry(name: str, columns: list[str]) -> DatasetCatalogEntry:
    return DatasetCatalogEntry(
        dataset_id=uuid.uuid4(),
        display_name=name,
        physical_table_name=f"ds_{name}",
        row_count=10,
        columns=[ColumnCatalogEntry(c, f"col_{i}", "string", False) for i, c in enumerate(columns)],
    )


async def test_prompt_only_includes_datasets_selected_by_the_plan():
    catalog = DatasetCatalog(
        entries=[
            _entry("orders", ["order_id", "customer_id"]),
            _entry("products", ["product_id", "brand"]),
        ],
        relationships=[RelationshipHint("orders", "product_id", "products", "product_id")],
    )
    plan = AnalysisPlan(
        intent=AnalyticalIntent(question_type="aggregation", metrics=[], dimensions=[], datasets=["orders"]),
        steps=["Count orders."],
    )
    llm = FakeLLMProvider()
    llm.queue_structured(SQLProposal(sql="SELECT COUNT(*) FROM orders"))

    await SqlGenerationService(llm).generate_sql(question="How many orders?", plan=plan, catalog=catalog)

    prompt, response_model = llm.structured_calls[0]
    assert response_model is SQLProposal
    assert "orders" in prompt
    assert "products" not in prompt  # not selected by the plan
    assert "ds_orders" not in prompt  # never the physical identifier


async def test_correction_prompt_includes_previous_sql_and_error():
    catalog = DatasetCatalog(entries=[_entry("orders", ["order_id"])], relationships=[])
    plan = AnalysisPlan(
        intent=AnalyticalIntent(question_type="aggregation", metrics=[], dimensions=[], datasets=["orders"]),
        steps=["Count orders."],
    )
    llm = FakeLLMProvider()
    llm.queue_structured(SQLProposal(sql="SELECT COUNT(*) FROM orders"))

    await SqlGenerationService(llm).generate_sql(
        question="How many orders?",
        plan=plan,
        catalog=catalog,
        previous_sql="SELECT * FROM orders; DROP TABLE orders;",
        error_feedback="Only a single SELECT statement is allowed.",
    )

    prompt, _ = llm.structured_calls[0]
    assert "DROP TABLE orders" in prompt
    assert "Only a single SELECT statement is allowed." in prompt
