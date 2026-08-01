import uuid

import pytest_asyncio

from app.application.retrieval.vector_search_service import VectorSearchService
from app.domain.data_source import SourceType
from app.domain.document import DocumentType
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.embeddings.base import EmbeddingTaskType


class _StubEmbeddingProvider:
    """Always returns the same fixed vector for the query — lets the test
    control ranking precisely, unlike the hash-based FakeEmbeddingProvider."""

    def __init__(self, query_vector: list[float]) -> None:
        self._query_vector = query_vector

    async def embed_batch(self, texts: list[str], *, task_type: EmbeddingTaskType) -> list[list[float]]:
        return [self._query_vector for _ in texts]


async def _make_document(db_session, workspace, title: str):
    data_source = await DataSourceRepository(db_session).create(
        workspace_id=workspace.id,
        name=title,
        source_type=SourceType.PDF,
        original_filename=f"{title}.pdf",
        mime_type="application/pdf",
        file_size_bytes=100,
        storage_key=f"{workspace.id}/{uuid.uuid4()}.pdf",
    )
    document = await DocumentRepository(db_session).create(
        workspace_id=workspace.id,
        data_source_id=data_source.id,
        title=title,
        document_type=DocumentType.PDF,
        text_content="irrelevant",
        page_count=1,
        language=None,
        metadata={},
    )
    await db_session.commit()
    return document


@pytest_asyncio.fixture
async def other_workspace(db_session):
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.database.repositories.user_repository import UserRepository
    from app.infrastructure.database.repositories.workspace_repository import WorkspaceRepository

    user = await UserRepository(db_session).create(
        email=f"other-{uuid.uuid4().hex[:8]}@example.com", hashed_password=PasswordHasher().hash("s3cret-pass")
    )
    workspace = await WorkspaceRepository(db_session).create(
        name="Other Workspace", slug=f"other-{uuid.uuid4().hex[:8]}", owner_id=user.id
    )
    await db_session.commit()
    return workspace


async def test_search_ranks_closest_chunk_first_and_resolves_document_title(
    db_session, seeded_workspace
):
    document = await _make_document(db_session, seeded_workspace, "Shipping Policy")
    chunk_repo = DocumentChunkRepository(db_session)
    query_vector = [1.0] + [0.0] * 767
    close_vector = [0.9] + [0.1] * 767
    far_vector = [0.0, 1.0] + [0.0] * 766

    created = await chunk_repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=document.id,
        chunks=[
            {
                "chunk_index": 0,
                "content": "Close match content.",
                "page_number": 1,
                "section_title": None,
                "token_count": 5,
                "metadata": {},
            },
            {
                "chunk_index": 1,
                "content": "Far match content.",
                "page_number": 2,
                "section_title": None,
                "token_count": 5,
                "metadata": {},
            },
        ],
    )
    await chunk_repo.set_embedding(created[0].id, embedding=close_vector, embedding_model="m", embedding_version="v")
    await chunk_repo.set_embedding(created[1].id, embedding=far_vector, embedding_model="m", embedding_version="v")
    await db_session.commit()

    service = VectorSearchService(chunk_repo, DocumentRepository(db_session), _StubEmbeddingProvider(query_vector))
    results = await service.search(workspace_id=seeded_workspace.id, query="What is the delivery window?", limit=5)

    assert len(results) == 2
    assert results[0].content == "Close match content."
    assert results[0].document_title == "Shipping Policy"
    assert results[0].scores.vector > results[1].scores.vector


async def test_search_never_returns_another_workspaces_chunks(
    db_session, seeded_workspace, other_workspace
):
    own_document = await _make_document(db_session, seeded_workspace, "Own Doc")
    other_document = await _make_document(db_session, other_workspace, "Other Doc")
    chunk_repo = DocumentChunkRepository(db_session)
    vector = [1.0] + [0.0] * 767

    own_chunks = await chunk_repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=own_document.id,
        chunks=[
            {
                "chunk_index": 0,
                "content": "Belongs to seeded_workspace.",
                "page_number": 1,
                "section_title": None,
                "token_count": 5,
                "metadata": {},
            }
        ],
    )
    other_chunks = await chunk_repo.bulk_create(
        workspace_id=other_workspace.id,
        document_id=other_document.id,
        chunks=[
            {
                "chunk_index": 0,
                "content": "Belongs to other_workspace.",
                "page_number": 1,
                "section_title": None,
                "token_count": 5,
                "metadata": {},
            }
        ],
    )
    await chunk_repo.set_embedding(own_chunks[0].id, embedding=vector, embedding_model="m", embedding_version="v")
    await chunk_repo.set_embedding(other_chunks[0].id, embedding=vector, embedding_model="m", embedding_version="v")
    await db_session.commit()

    service = VectorSearchService(chunk_repo, DocumentRepository(db_session), _StubEmbeddingProvider(vector))
    results = await service.search(workspace_id=seeded_workspace.id, query="anything", limit=5)

    assert len(results) == 1
    assert results[0].content == "Belongs to seeded_workspace."


async def test_search_returns_empty_list_when_no_chunks_are_embedded(db_session, seeded_workspace):
    document = await _make_document(db_session, seeded_workspace, "Empty Doc")
    chunk_repo = DocumentChunkRepository(db_session)
    await chunk_repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=document.id,
        chunks=[
            {
                "chunk_index": 0,
                "content": "Not embedded yet.",
                "page_number": 1,
                "section_title": None,
                "token_count": 5,
                "metadata": {},
            }
        ],
    )
    await db_session.commit()

    service = VectorSearchService(
        chunk_repo, DocumentRepository(db_session), _StubEmbeddingProvider([1.0] + [0.0] * 767)
    )
    results = await service.search(workspace_id=seeded_workspace.id, query="anything", limit=5)

    assert results == []
