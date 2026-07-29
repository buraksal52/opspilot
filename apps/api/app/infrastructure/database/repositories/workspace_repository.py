import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.workspace import Workspace
from app.infrastructure.database.models.workspace import WorkspaceModel


def _to_domain(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        name=model.name,
        slug=model.slug,
        owner_id=model.owner_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        model = await self._session.get(WorkspaceModel, workspace_id)
        return _to_domain(model) if model else None

    async def create(self, *, name: str, slug: str, owner_id: uuid.UUID) -> Workspace:
        model = WorkspaceModel(name=name, slug=slug, owner_id=owner_id)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)
