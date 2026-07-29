import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.service import AuthService
from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, UnauthorizedError
from app.domain.user import User
from app.domain.workspace import Workspace
from app.infrastructure.auth.jwt_provider import JWTProvider, TokenError
from app.infrastructure.auth.password_hasher import PasswordHasher
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository
from app.infrastructure.database.session import get_db

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
