import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt

from app.core.config import get_settings
from app.infrastructure.auth.jwt_provider import JWTProvider


def _jwt_provider() -> JWTProvider:
    settings = get_settings()
    return JWTProvider(settings.jwt_secret_key, settings.jwt_algorithm, settings.jwt_access_token_expire_minutes)


async def test_login_success_returns_valid_bearer_token(client, seeded_user):
    user, password = seeded_user

    response = await client.post("/api/v1/auth/login", json={"email": user.email, "password": password})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"

    settings = get_settings()
    payload = pyjwt.decode(body["access_token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == str(user.id)


async def test_login_wrong_password_is_rejected(client, seeded_user):
    user, _password = seeded_user

    response = await client.post("/api/v1/auth/login", json={"email": user.email, "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_login_unknown_email_is_rejected(client):
    response = await client.post(
        "/api/v1/auth/login", json={"email": "nobody-registered@example.com", "password": "whatever"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_protected_route_without_token_is_rejected(client, seeded_workspace):
    response = await client.get(f"/api/v1/workspaces/{seeded_workspace.id}")

    assert response.status_code == 401


async def test_protected_route_with_malformed_token_is_rejected(client, seeded_workspace):
    response = await client.get(
        f"/api/v1/workspaces/{seeded_workspace.id}",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


async def test_protected_route_with_expired_token_is_rejected(client, seeded_user, seeded_workspace):
    user, _password = seeded_user
    settings = get_settings()
    now = datetime.now(UTC)
    expired_token = pyjwt.encode(
        {"sub": str(user.id), "iat": now - timedelta(minutes=60), "exp": now - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(
        f"/api/v1/workspaces/{seeded_workspace.id}",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


async def test_owner_can_access_own_workspace(client, seeded_user, seeded_workspace):
    user, _password = seeded_user
    token = _jwt_provider().create_access_token(user.id)

    response = await client.get(
        f"/api/v1/workspaces/{seeded_workspace.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(seeded_workspace.id)


async def test_cross_workspace_access_is_denied(client, db_session, seeded_workspace):
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.database.repositories.user_repository import UserRepository

    other_user = await UserRepository(db_session).create(
        email=f"other-{uuid.uuid4().hex[:12]}@example.com",
        hashed_password=PasswordHasher().hash("another-password"),
    )
    await db_session.commit()
    token = _jwt_provider().create_access_token(other_user.id)

    response = await client.get(
        f"/api/v1/workspaces/{seeded_workspace.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_unknown_workspace_id_returns_not_found(client, seeded_user):
    user, _password = seeded_user
    token = _jwt_provider().create_access_token(user.id)

    response = await client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
