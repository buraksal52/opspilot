from fastapi import APIRouter, Depends

from app.api.v1.deps import require_workspace_access
from app.api.v1.schemas.workspace import WorkspaceResponse
from app.domain.workspace import Workspace

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace: Workspace = Depends(require_workspace_access)) -> WorkspaceResponse:
    return WorkspaceResponse(id=workspace.id, name=workspace.name, slug=workspace.slug, owner_id=workspace.owner_id)
