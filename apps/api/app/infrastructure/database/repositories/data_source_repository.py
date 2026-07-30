import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.data_source import DataSource, DataSourceStatus, SourceType
from app.infrastructure.database.models.data_source import DataSourceModel


def _to_domain(model: DataSourceModel) -> DataSource:
    return DataSource(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        source_type=SourceType(model.source_type),
        original_filename=model.original_filename,
        mime_type=model.mime_type,
        file_size_bytes=model.file_size_bytes,
        status=DataSourceStatus(model.status),
        storage_key=model.storage_key,
        error_message=model.error_message,
        source_metadata=model.source_metadata,
        created_at=model.created_at,
        updated_at=model.updated_at,
        processed_at=model.processed_at,
    )


class DataSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, data_source_id: uuid.UUID) -> DataSource | None:
        model = await self._session.get(DataSourceModel, data_source_id)
        return _to_domain(model) if model else None

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[DataSource]:
        result = await self._session.execute(
            select(DataSourceModel)
            .where(DataSourceModel.workspace_id == workspace_id, DataSourceModel.status != DataSourceStatus.DELETED.value)
            .order_by(DataSourceModel.created_at.desc())
        )
        return [_to_domain(m) for m in result.scalars().all()]

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        name: str,
        source_type: SourceType,
        original_filename: str,
        mime_type: str,
        file_size_bytes: int,
        storage_key: str,
        id: uuid.UUID | None = None,
    ) -> DataSource:
        # Callers that need to know the id before the row is flushed (e.g. to
        # build a storage_key that embeds the data_source_id) may pass one in
        # explicitly; otherwise the column default generates one.
        model = DataSourceModel(
            id=id or uuid.uuid4(),
            workspace_id=workspace_id,
            name=name,
            source_type=source_type.value,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            status=DataSourceStatus.UPLOADED.value,
            storage_key=storage_key,
            source_metadata={},
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def update_status(
        self,
        data_source_id: uuid.UUID,
        *,
        status: DataSourceStatus,
        error_message: str | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        model = await self._session.get(DataSourceModel, data_source_id)
        if model is None:
            raise ValueError(f"DataSource {data_source_id} not found")
        model.status = status.value
        model.error_message = error_message
        if processed_at is not None:
            model.processed_at = processed_at
        await self._session.flush()
