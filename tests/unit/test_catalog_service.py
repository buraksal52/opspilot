import uuid
from datetime import datetime, timezone

from app.application.analytics.catalog_service import DatasetCatalogService
from app.domain.dataset import ColumnDefinition, Dataset, DatasetStatus

WORKSPACE_ID = uuid.uuid4()


def _dataset(name: str, columns: list[str], *, status: DatasetStatus = DatasetStatus.READY, row_count: int = 10) -> Dataset:
    now = datetime.now(timezone.utc)
    return Dataset(
        id=uuid.uuid4(),
        workspace_id=WORKSPACE_ID,
        data_source_id=uuid.uuid4(),
        name=name,
        description=None,
        physical_table_name=f"ds_{uuid.uuid4().hex}",
        row_count=row_count,
        column_count=len(columns),
        schema_definition=[
            ColumnDefinition(display_name=col, physical_name=f"col_{i + 1}", type="string", nullable=False)
            for i, col in enumerate(columns)
        ],
        profile_statistics={},
        status=status,
        created_at=now,
        updated_at=now,
    )


class _FakeDatasetRepository:
    def __init__(self, datasets: list[Dataset]) -> None:
        self._datasets = datasets

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Dataset]:
        return [d for d in self._datasets if d.workspace_id == workspace_id]


async def test_catalog_exposes_only_ready_datasets_with_display_names():
    datasets = [
        _dataset("orders", ["order_id", "customer_id"]),
        _dataset("refunds", ["refund_id", "order_id"], status=DatasetStatus.PROCESSING),
    ]
    catalog = await DatasetCatalogService(_FakeDatasetRepository(datasets)).get_catalog(WORKSPACE_ID)

    assert [e.display_name for e in catalog.entries] == ["orders"]
    assert catalog.get("ORDERS") is not None  # case-insensitive lookup
    assert catalog.get("orders").column("customer_id").physical_name == "col_2"


async def test_relationships_only_included_when_both_datasets_present():
    datasets = [_dataset("orders", ["order_id", "customer_id", "product_id"])]
    catalog = await DatasetCatalogService(_FakeDatasetRepository(datasets)).get_catalog(WORKSPACE_ID)

    # customers/products aren't in this workspace's catalog, so no relationship
    # referencing them should be surfaced even though orders has the columns.
    assert catalog.relationships == []


async def test_relationship_surfaced_when_both_sides_present():
    datasets = [
        _dataset("orders", ["order_id", "customer_id"]),
        _dataset("customers", ["customer_id"]),
    ]
    catalog = await DatasetCatalogService(_FakeDatasetRepository(datasets)).get_catalog(WORKSPACE_ID)

    assert len(catalog.relationships) == 1
    assert catalog.relationships[0].from_dataset == "orders"
    assert catalog.relationships[0].to_dataset == "customers"


async def test_duplicate_display_name_keeps_most_recently_created():
    older = _dataset("orders", ["order_id"])
    newer = _dataset("orders", ["order_id", "customer_id"])
    # list_by_workspace orders by created_at desc; simulate that ordering directly.
    catalog = await DatasetCatalogService(_FakeDatasetRepository([newer, older])).get_catalog(WORKSPACE_ID)

    assert len(catalog.entries) == 1
    assert catalog.entries[0].dataset_id == newer.id


def test_render_only_shows_display_names():
    entry_columns = ["order_id", "customer_id"]
    catalog_service_columns = [
        ColumnDefinition(display_name=c, physical_name=f"col_{i}", type="string", nullable=False)
        for i, c in enumerate(entry_columns)
    ]
    from app.application.analytics.catalog_service import ColumnCatalogEntry, DatasetCatalog, DatasetCatalogEntry

    catalog = DatasetCatalog(
        entries=[
            DatasetCatalogEntry(
                dataset_id=uuid.uuid4(),
                display_name="orders",
                physical_table_name="ds_should_never_appear",
                row_count=5,
                columns=[ColumnCatalogEntry(c.display_name, c.physical_name, c.type, c.nullable) for c in catalog_service_columns],
            )
        ],
        relationships=[],
    )

    rendered = catalog.render()
    assert "ds_should_never_appear" not in rendered
    assert "col_0" not in rendered
    assert "orders" in rendered
    assert "customer_id" in rendered
