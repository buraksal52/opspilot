import os

# Must be set before any `app.*` module is imported: app.core.config.get_settings()
# is cached, and app.infrastructure.database.session builds its engine at
# import time from those settings.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://opspilot:opspilot@localhost:55432/opspilot")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-do-not-use-in-prod")
os.environ.setdefault("REDIS_URL", "redis://localhost:63790/0")

import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

API_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api"
TEST_DATABASE_URL = os.environ["DATABASE_URL"]


def _alembic_config() -> Config:
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    return cfg


@pytest.fixture(scope="session", autouse=True)
def _migrated_database():
    """Run real Alembic migrations once for the test session (not metadata.create_all)."""
    cfg = _alembic_config()
    command.upgrade(cfg, "head")
    yield
    command.downgrade(cfg, "base")


@pytest_asyncio.fixture
async def db_session():
    from app.infrastructure.database.session import async_session_factory

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


@pytest_asyncio.fixture
async def seeded_user(db_session, unique_email):
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.database.repositories.user_repository import UserRepository

    password = "correct-horse-battery-staple"
    hasher = PasswordHasher()
    user = await UserRepository(db_session).create(email=unique_email, hashed_password=hasher.hash(password))
    await db_session.commit()
    return user, password


@pytest_asyncio.fixture
async def seeded_workspace(db_session, seeded_user):
    from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository

    user, _password = seeded_user
    workspace = await WorkspaceRepository(db_session).create(
        name="Northstar Commerce", slug=f"ws-{uuid.uuid4().hex[:8]}", owner_id=user.id
    )
    await db_session.commit()
    return workspace
