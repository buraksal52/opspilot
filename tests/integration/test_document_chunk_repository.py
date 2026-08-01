import uuid

import pytest
import pytest_asyncio

from app.domain.data_source import SourceType
from app.domain.document import DocumentType
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.database.repositories.document_repository import DocumentRepository


@pytest_asyncio.fixture
async def seeded_document(db_session, seeded_workspace):
    data_source = await DataSourceRepository(db_session).create(
        workspace_id=seeded_workspace.id,
        name="Shipping Policy",
        source_type=SourceType.PDF,
        original_filename="Shipping Policy.pdf",
        mime_type="application/pdf",
        file_size_bytes=1234,
        storage_key=f"{seeded_workspace.id}/{uuid.uuid4()}.pdf",
    )
    document = await DocumentRepository(db_session).create(
        workspace_id=seeded_workspace.id,
        data_source_id=data_source.id,
        title="Shipping Policy",
        document_type=DocumentType.PDF,
        text_content="Standard delivery takes 2-4 business days.",
        page_count=1,
        language=None,
        metadata={},
    )
    await db_session.commit()
    return document


def _chunk_dict(index: int, content: str) -> dict:
    return {
        "chunk_index": index,
        "content": content,
        "page_number": 1,
        "section_title": None,
        "token_count": len(content) // 4,
        "metadata": {},
    }


async def test_bulk_create_and_list_by_document(db_session, seeded_workspace, seeded_document):
    repo = DocumentChunkRepository(db_session)

    created = await repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=seeded_document.id,
        chunks=[_chunk_dict(0, "First chunk."), _chunk_dict(1, "Second chunk.")],
    )
    await db_session.commit()

    assert len(created) == 2
    assert all(chunk.embedding is None for chunk in created)

    listed = await repo.list_by_document(seeded_document.id)
    assert [c.chunk_index for c in listed] == [0, 1]


async def test_list_missing_embeddings_and_set_embedding(db_session, seeded_workspace, seeded_document):
    repo = DocumentChunkRepository(db_session)
    created = await repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=seeded_document.id,
        chunks=[_chunk_dict(0, "Needs an embedding.")],
    )
    await db_session.commit()

    missing = await repo.list_missing_embeddings(seeded_document.id)
    assert len(missing) == 1

    vector = [0.1] * 768
    await repo.set_embedding(
        created[0].id, embedding=vector, embedding_model="gemini-embedding-001", embedding_version="768d-v1"
    )
    await db_session.commit()

    missing_after = await repo.list_missing_embeddings(seeded_document.id)
    assert missing_after == []


async def test_search_by_embedding_is_workspace_scoped_and_ranked(db_session, seeded_workspace, seeded_document):
    repo = DocumentChunkRepository(db_session)
    created = await repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=seeded_document.id,
        chunks=[_chunk_dict(0, "Close match."), _chunk_dict(1, "Far match.")],
    )
    await db_session.commit()

    close_vector = [1.0] + [0.0] * 767
    far_vector = [0.0, 1.0] + [0.0] * 766
    await repo.set_embedding(created[0].id, embedding=close_vector, embedding_model="m", embedding_version="v")
    await repo.set_embedding(created[1].id, embedding=far_vector, embedding_model="m", embedding_version="v")
    await db_session.commit()

    results = await repo.search_by_embedding(
        workspace_id=seeded_workspace.id, query_embedding=close_vector, limit=5
    )

    assert len(results) == 2
    assert results[0][0].id == created[0].id
    assert results[0][1] < results[1][1]  # cosine distance: closer match ranks first


async def test_search_by_text_finds_matching_keyword_and_ranks_relevance(db_session, seeded_workspace, seeded_document):
    repo = DocumentChunkRepository(db_session)
    await repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=seeded_document.id,
        chunks=[
            _chunk_dict(0, "Standard delivery takes 2-4 business days for most orders."),
            _chunk_dict(1, "Refunds are processed within five business days of approval."),
        ],
    )
    await db_session.commit()

    results = await repo.search_by_text(workspace_id=seeded_workspace.id, query="delivery", limit=5)

    assert len(results) == 1
    assert "delivery" in results[0][0].content.lower()


async def test_search_by_text_excludes_non_matching_chunks(db_session, seeded_workspace, seeded_document):
    repo = DocumentChunkRepository(db_session)
    await repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=seeded_document.id,
        chunks=[_chunk_dict(0, "This paragraph is entirely about warehouse staffing schedules.")],
    )
    await db_session.commit()

    results = await repo.search_by_text(workspace_id=seeded_workspace.id, query="refund policy", limit=5)

    assert results == []


async def test_search_by_text_is_workspace_scoped(db_session, seeded_workspace, seeded_document):
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.database.repositories.user_repository import UserRepository
    from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository

    repo = DocumentChunkRepository(db_session)
    await repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=seeded_document.id,
        chunks=[_chunk_dict(0, "Shipping provider migration happened in July.")],
    )
    await db_session.commit()

    other_user = await UserRepository(db_session).create(
        email=f"other-{uuid.uuid4().hex[:8]}@example.com", hashed_password=PasswordHasher().hash("s3cret-pass")
    )
    other_workspace = await WorkspaceRepository(db_session).create(
        name="Other Workspace", slug=f"other-{uuid.uuid4().hex[:8]}", owner_id=other_user.id
    )
    await db_session.commit()

    results = await repo.search_by_text(workspace_id=other_workspace.id, query="shipping provider migration", limit=5)

    assert results == []


async def test_search_by_embedding_excludes_other_workspaces(db_session, seeded_workspace, seeded_document):
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.database.repositories.user_repository import UserRepository
    from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository

    repo = DocumentChunkRepository(db_session)
    vector = [1.0] + [0.0] * 767
    created = await repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=seeded_document.id,
        chunks=[_chunk_dict(0, "Belongs to workspace A.")],
    )
    await repo.set_embedding(created[0].id, embedding=vector, embedding_model="m", embedding_version="v")
    await db_session.commit()

    other_user = await UserRepository(db_session).create(
        email=f"other-{uuid.uuid4().hex[:8]}@example.com", hashed_password=PasswordHasher().hash("s3cret-pass")
    )
    other_workspace = await WorkspaceRepository(db_session).create(
        name="Other Workspace", slug=f"other-{uuid.uuid4().hex[:8]}", owner_id=other_user.id
    )
    await db_session.commit()

    results = await repo.search_by_embedding(workspace_id=other_workspace.id, query_embedding=vector, limit=5)

    assert results == []
