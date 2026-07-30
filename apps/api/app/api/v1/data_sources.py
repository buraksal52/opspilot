from fastapi import APIRouter, Depends, UploadFile

from app.api.v1.deps import get_data_source_repository, get_upload_service, require_data_source_access, require_workspace_access
from app.api.v1.schemas.data_source import DataSourceResponse
from app.application.ingestion.upload_service import UploadService
from app.core.config import get_settings
from app.core.errors import ValidationAppError
from app.domain.data_source import DataSource, DataSourceStatus
from app.domain.workspace import Workspace
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository

router = APIRouter(tags=["data-sources"])


def _to_response(data_source: DataSource) -> DataSourceResponse:
    return DataSourceResponse(
        id=data_source.id,
        workspace_id=data_source.workspace_id,
        name=data_source.name,
        source_type=data_source.source_type.value,
        original_filename=data_source.original_filename,
        mime_type=data_source.mime_type,
        file_size_bytes=data_source.file_size_bytes,
        status=data_source.status.value,
        error_message=data_source.error_message,
        created_at=data_source.created_at,
        updated_at=data_source.updated_at,
        processed_at=data_source.processed_at,
    )


async def _read_within_limit(file: UploadFile, max_size_bytes: int) -> bytes:
    """Reads the upload in chunks, aborting as soon as the limit is exceeded
    rather than buffering an unbounded body first (SECURITY.md §20, §32)."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_size_bytes:
            raise ValidationAppError(f"File exceeds the maximum upload size of {max_size_bytes} bytes.")
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/workspaces/{workspace_id}/data-sources/upload", response_model=DataSourceResponse)
async def upload_data_source(
    file: UploadFile,
    workspace: Workspace = Depends(require_workspace_access),
    upload_service: UploadService = Depends(get_upload_service),
) -> DataSourceResponse:
    max_size_bytes = get_settings().upload_max_size_bytes
    content = await _read_within_limit(file, max_size_bytes)

    data_source = await upload_service.upload(
        workspace_id=workspace.id,
        filename=file.filename or "upload",
        content_type=file.content_type,
        content=content,
    )
    return _to_response(data_source)


@router.get("/workspaces/{workspace_id}/data-sources", response_model=list[DataSourceResponse])
async def list_data_sources(
    workspace: Workspace = Depends(require_workspace_access),
    data_source_repository: DataSourceRepository = Depends(get_data_source_repository),
) -> list[DataSourceResponse]:
    data_sources = await data_source_repository.list_by_workspace(workspace.id)
    return [_to_response(ds) for ds in data_sources]


@router.get("/data-sources/{data_source_id}", response_model=DataSourceResponse)
async def get_data_source(data_source: DataSource = Depends(require_data_source_access)) -> DataSourceResponse:
    return _to_response(data_source)


@router.delete("/data-sources/{data_source_id}", status_code=204)
async def delete_data_source(
    data_source: DataSource = Depends(require_data_source_access),
    data_source_repository: DataSourceRepository = Depends(get_data_source_repository),
) -> None:
    await data_source_repository.update_status(data_source.id, status=DataSourceStatus.DELETED)
