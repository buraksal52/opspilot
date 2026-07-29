import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.infrastructure.auth.password_hasher import PasswordHasher
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository


async def test_workspace_persists_and_can_be_loaded_by_id(db_session, unique_email):
    user = await UserRepository(db_session).create(
        email=unique_email, hashed_password=PasswordHasher().hash("s3cret-pass")
    )
    created = await WorkspaceRepository(db_session).create(
        name="Northstar Commerce", slug=f"northstar-{uuid.uuid4().hex[:8]}", owner_id=user.id
    )
    await db_session.commit()

    fetched = await WorkspaceRepository(db_session).get_by_id(created.id)

    assert fetched is not None
    assert fetched.name == "Northstar Commerce"
    assert fetched.owner_id == user.id


async def test_workspace_slug_must_be_unique(db_session, unique_email):
    user = await UserRepository(db_session).create(
        email=unique_email, hashed_password=PasswordHasher().hash("s3cret-pass")
    )
    slug = f"dup-{uuid.uuid4().hex[:8]}"
    await WorkspaceRepository(db_session).create(name="A", slug=slug, owner_id=user.id)
    await db_session.commit()

    with pytest.raises(IntegrityError):
        await WorkspaceRepository(db_session).create(name="B", slug=slug, owner_id=user.id)


async def test_workspace_requires_existing_owner(db_session):
    with pytest.raises(IntegrityError):
        await WorkspaceRepository(db_session).create(
            name="Orphan", slug=f"orphan-{uuid.uuid4().hex[:8]}", owner_id=uuid.uuid4()
        )
