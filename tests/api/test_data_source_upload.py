import io
import uuid

from sqlalchemy import text

from app.core.config import get_settings
from app.infrastructure.auth.jwt_provider import JWTProvider

SAMPLE_CSV = b"order_id,amount,order_date\nORD-1,10.5,2024-07-01\nORD-2,20,2024-07-12\n"
SAMPLE_MARKDOWN = b"# Policy\n\nStandard delivery window is 2-4 business days.\n"
SAMPLE_TEXT = b"Plain text support ticket content.\n"


def _jwt_provider() -> JWTProvider:
    settings = get_settings()
    return JWTProvider(settings.jwt_secret_key, settings.jwt_algorithm, settings.jwt_access_token_expire_minutes)


def _auth_headers(user_id) -> dict[str, str]:
    token = _jwt_provider().create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _minimal_pdf_bytes() -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, "Standard delivery window is 2-4 business days.")
    return bytes(pdf.output())


async def test_upload_csv_creates_ready_dataset(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("orders.csv", SAMPLE_CSV, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "CSV"
    assert body["status"] == "READY"
    assert body["error_message"] is None
    assert body["name"] == "orders"


async def test_upload_pdf_creates_ready_document(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("Shipping Policy.pdf", _minimal_pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "PDF"
    assert body["status"] == "READY"


async def test_upload_markdown_creates_ready_document(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("policy.md", SAMPLE_MARKDOWN, "text/markdown")},
    )

    assert response.status_code == 200
    assert response.json()["source_type"] == "MARKDOWN"
    assert response.json()["status"] == "READY"


async def test_upload_text_creates_ready_document(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("ticket.txt", SAMPLE_TEXT, "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["source_type"] == "TEXT"
    assert response.json()["status"] == "READY"


async def test_upload_without_auth_is_rejected(client, seeded_workspace):
    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        files={"file": ("orders.csv", SAMPLE_CSV, "text/csv")},
    )
    assert response.status_code == 401


async def test_upload_unsupported_extension_is_rejected(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("archive.zip", b"not-a-real-zip", "application/zip")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_upload_fake_pdf_is_rejected_by_magic_bytes(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("report.pdf", b"this is just text, not a pdf", "application/pdf")},
    )
    assert response.status_code == 422


async def test_upload_oversized_file_is_rejected(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    settings = get_settings()
    oversized = b"a" * (settings.upload_max_size_bytes + 1)

    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("huge.txt", oversized, "text/plain")},
    )
    assert response.status_code == 422


async def test_malformed_csv_uploads_successfully_but_dataset_ingestion_fails(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    malformed_csv = b"a,b,c\n1,2\n"  # ragged row: 2 values for 3 columns

    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("bad.csv", malformed_csv, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["error_message"] is not None


async def test_malicious_csv_header_round_trips_safely_through_real_postgres(
    client, db_session, seeded_user, seeded_workspace
):
    user, _ = seeded_user
    malicious_csv = io.StringIO()
    import csv

    writer = csv.writer(malicious_csv)
    writer.writerow(['"; DROP TABLE analytics.orders; --', "amount"])
    writer.writerow(["SwiftShip", "10"])

    response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("evil.csv", malicious_csv.getvalue().encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "READY"

    result = await db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'analytics'")
    )
    table_names = [row[0] for row in result.all()]
    assert any(name.startswith("ds_") for name in table_names)
    assert not any("DROP TABLE" in name for name in table_names)

    result = await db_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'analytics' AND table_name = ANY(:names)"
        ),
        {"names": [n for n in table_names if n.startswith("ds_")]},
    )
    column_names = [row[0] for row in result.all()]
    assert all(name.startswith("col_") for name in column_names)
    assert not any("DROP TABLE" in name for name in column_names)


async def test_list_data_sources_returns_uploaded_items(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("orders.csv", SAMPLE_CSV, "text/csv")},
    )

    response = await client.get(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources", headers=_auth_headers(user.id)
    )

    assert response.status_code == 200
    names = [ds["name"] for ds in response.json()]
    assert "orders" in names


async def test_get_and_delete_data_source(client, seeded_user, seeded_workspace):
    user, _ = seeded_user
    upload_response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("orders.csv", SAMPLE_CSV, "text/csv")},
    )
    data_source_id = upload_response.json()["id"]

    get_response = await client.get(f"/api/v1/data-sources/{data_source_id}", headers=_auth_headers(user.id))
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "READY"

    delete_response = await client.delete(f"/api/v1/data-sources/{data_source_id}", headers=_auth_headers(user.id))
    assert delete_response.status_code == 204

    list_response = await client.get(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources", headers=_auth_headers(user.id)
    )
    assert data_source_id not in [ds["id"] for ds in list_response.json()]


async def test_cross_workspace_data_source_access_is_denied(client, db_session, seeded_user, seeded_workspace):
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.database.repositories.user_repository import UserRepository

    user, _ = seeded_user
    upload_response = await client.post(
        f"/api/v1/workspaces/{seeded_workspace.id}/data-sources/upload",
        headers=_auth_headers(user.id),
        files={"file": ("orders.csv", SAMPLE_CSV, "text/csv")},
    )
    data_source_id = upload_response.json()["id"]

    other_user = await UserRepository(db_session).create(
        email=f"other-{uuid.uuid4().hex[:12]}@example.com",
        hashed_password=PasswordHasher().hash("another-password"),
    )
    await db_session.commit()

    response = await client.get(f"/api/v1/data-sources/{data_source_id}", headers=_auth_headers(other_user.id))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

    delete_response = await client.delete(
        f"/api/v1/data-sources/{data_source_id}", headers=_auth_headers(other_user.id)
    )
    assert delete_response.status_code == 404


async def test_unknown_data_source_id_returns_not_found(client, seeded_user):
    user, _ = seeded_user
    response = await client.get(f"/api/v1/data-sources/{uuid.uuid4()}", headers=_auth_headers(user.id))
    assert response.status_code == 404
