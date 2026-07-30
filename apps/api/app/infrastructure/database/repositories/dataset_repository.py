import uuid
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.dataset import ColumnDefinition, Dataset, DatasetStatus
from app.infrastructure.database.models.dataset import DatasetModel


def _to_domain(model: DatasetModel) -> Dataset:
    return Dataset(
        id=model.id,
        workspace_id=model.workspace_id,
        data_source_id=model.data_source_id,
        name=model.name,
        description=model.description,
        physical_table_name=model.physical_table_name,
        row_count=model.row_count,
        column_count=model.column_count,
        schema_definition=[ColumnDefinition(**col) for col in model.schema_definition],
        profile_statistics=model.profile_statistics,
        status=DatasetStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class DatasetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, dataset_id: uuid.UUID) -> Dataset | None:
        model = await self._session.get(DatasetModel, dataset_id)
        return _to_domain(model) if model else None

    async def get_by_data_source_id(self, data_source_id: uuid.UUID) -> Dataset | None:
        result = await self._session.execute(select(DatasetModel).where(DatasetModel.data_source_id == data_source_id))
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Dataset]:
        result = await self._session.execute(
            select(DatasetModel).where(DatasetModel.workspace_id == workspace_id).order_by(DatasetModel.created_at.desc())
        )
        return [_to_domain(m) for m in result.scalars().all()]

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        data_source_id: uuid.UUID,
        name: str,
        description: str | None,
        physical_table_name: str,
        row_count: int,
        column_count: int,
        schema_definition: list[ColumnDefinition],
        profile_statistics: dict,
        id: uuid.UUID | None = None,
    ) -> Dataset:
        # As with DataSourceRepository.create: the caller generates the id
        # upfront here because physical_table_name (ADR-017) is derived from
        # it before the row exists.
        model = DatasetModel(
            id=id or uuid.uuid4(),
            workspace_id=workspace_id,
            data_source_id=data_source_id,
            name=name,
            description=description,
            physical_table_name=physical_table_name,
            row_count=row_count,
            column_count=column_count,
            schema_definition=[asdict(col) for col in schema_definition],
            profile_statistics=profile_statistics,
            status=DatasetStatus.READY.value,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)
