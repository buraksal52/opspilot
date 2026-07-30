import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.service import AuthService
from app.application.ingestion.dataset_ingestion_service import DatasetIngestionService
from app.application.ingestion.document_ingestion_service import DocumentIngestionService
from app.application.ingestion.upload_service import UploadService
from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, UnauthorizedError
from app.domain.data_source import DataSource
from app.domain.user import User
from app.domain.workspace import Workspace
from app.infrastructure.auth.jwt_provider import JWTProvider, TokenError
from app.infrastructure.auth.password_hasher import PasswordHasher
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository
from app.infrastructure.database.session import get_db
from app.infrastructure.storage.file_storage import FileStorage, LocalFileStorage

_bearer_scheme = HTTPBearer(auto_error=False)


def get_password_hasher() -> PasswordHasher:
    return PasswordHasher()


def get_jwt_provider(settings: Settings = Depends(get_settings)) -> JWTProvider:
    return JWTProvider(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
    )


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_workspace_repository(session: AsyncSession = Depends(get_db)) -> WorkspaceRepository:
    return WorkspaceRepository(session)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
) -> AuthService:
    return AuthService(user_repository, password_hasher, jwt_provider)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    jwt_provider: JWTProvider = Depends(get_jwt_provider),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token.")

    try:
        user_id = jwt_provider.decode_user_id(credentials.credentials)
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user = await user_repository.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User no longer exists.")

    return user


async def require_workspace_access(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace_repository: WorkspaceRepository = Depends(get_workspace_repository),
) -> Workspace:
    workspace = await workspace_repository.get_by_id(workspace_id)
    if workspace is None or workspace.owner_id != current_user.id:
        # Identical response whether the workspace doesn't exist or belongs to
        # someone else, so a resource id can't be used to probe existence
        # (SECURITY.md §4, §39 — fail closed).
        raise NotFoundError("The requested workspace does not exist.")

    return workspace


def get_file_storage(settings: Settings = Depends(get_settings)) -> FileStorage:
    return LocalFileStorage(settings.upload_base_dir)


def get_data_source_repository(session: AsyncSession = Depends(get_db)) -> DataSourceRepository:
    return DataSourceRepository(session)


def get_document_repository(session: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(session)


def get_document_ingestion_service(
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> DocumentIngestionService:
    return DocumentIngestionService(document_repository)


def get_dataset_ingestion_service(session: AsyncSession = Depends(get_db)) -> DatasetIngestionService:
    return DatasetIngestionService(session)


def get_upload_service(
    data_source_repository: DataSourceRepository = Depends(get_data_source_repository),
    file_storage: FileStorage = Depends(get_file_storage),
    document_ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
    dataset_ingestion_service: DatasetIngestionService = Depends(get_dataset_ingestion_service),
    settings: Settings = Depends(get_settings),
) -> UploadService:
    return UploadService(
        data_source_repository,
        file_storage,
        document_ingestion_service,
        dataset_ingestion_service,
        settings.upload_max_size_bytes,
    )


async def require_data_source_access(
    data_source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    data_source_repository: DataSourceRepository = Depends(get_data_source_repository),
    workspace_repository: WorkspaceRepository = Depends(get_workspace_repository),
) -> DataSource:
    data_source = await data_source_repository.get_by_id(data_source_id)
    if data_source is None:
        raise NotFoundError("The requested data source does not exist.")

    workspace = await workspace_repository.get_by_id(data_source.workspace_id)
    if workspace is None or workspace.owner_id != current_user.id:
        # Same fail-closed, identical-404 pattern as require_workspace_access.
        raise NotFoundError("The requested data source does not exist.")

    return data_source
