import os
import uuid

import pytest_asyncio

from app.application.retrieval.embedding_service import EMBEDDING_VERSION, EmbeddingGenerationService
from app.domain.data_source import SourceType
from app.domain.document import DocumentType
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.embeddings.fake_provider import FakeEmbeddingProvider
from app.infrastructure.jobs.queue import ArqJobQueue

TEST_REDIS_URL = os.environ["REDIS_URL"]


@pytest_asyncio.fixture
async def seeded_document(db_session, seeded_workspace):
    data_source = await DataSourceRepository(db_session).create(
        workspace_id=seeded_workspace.id,
        name="Refund Policy",
        source_type=SourceType.PDF,
        original_filename="Refund Policy.pdf",
        mime_type="application/pdf",
        file_size_bytes=1234,
        storage_key=f"{seeded_workspace.id}/{uuid.uuid4()}.pdf",
    )
    document = await DocumentRepository(db_session).create(
        workspace_id=seeded_workspace.id,
        data_source_id=data_source.id,
        title="Refund Policy",
        document_type=DocumentType.PDF,
        text_content="Refunds are issued within five business days of approval.",
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


async def test_generate_for_document_embeds_all_missing_chunks(db_session, seeded_workspace, seeded_document):
    chunk_repo = DocumentChunkRepository(db_session)
    await chunk_repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=seeded_document.id,
        chunks=[_chunk_dict(0, "First chunk of the refund policy."), _chunk_dict(1, "Second chunk about timelines.")],
    )
    await db_session.commit()

    service = EmbeddingGenerationService(chunk_repo, FakeEmbeddingProvider(dimension=768), "gemini-embedding-001")

    embedded_count = await service.generate_for_document(seeded_document.id)
    await db_session.commit()

    assert embedded_count == 2
    remaining = await chunk_repo.list_missing_embeddings(seeded_document.id)
    assert remaining == []

    all_chunks = await chunk_repo.list_by_document(seeded_document.id)
    assert all(chunk.embedding_model == "gemini-embedding-001" for chunk in all_chunks)
    assert all(chunk.embedding_version == EMBEDDING_VERSION for chunk in all_chunks)
    assert all(len(chunk.embedding) == 768 for chunk in all_chunks)


async def test_generate_for_document_is_a_no_op_when_nothing_is_missing(db_session, seeded_workspace, seeded_document):
    chunk_repo = DocumentChunkRepository(db_session)
    await chunk_repo.bulk_create(
        workspace_id=seeded_workspace.id, document_id=seeded_document.id, chunks=[_chunk_dict(0, "Only chunk.")]
    )
    await db_session.commit()

    service = EmbeddingGenerationService(chunk_repo, FakeEmbeddingProvider(dimension=768), "gemini-embedding-001")
    first_count = await service.generate_for_document(seeded_document.id)
    await db_session.commit()
    second_count = await service.generate_for_document(seeded_document.id)

    assert first_count == 1
    assert second_count == 0


async def test_arq_job_queue_enqueues_a_real_job_against_test_redis(seeded_document):
    """Verifies the enqueue call itself reaches Redis (ADR-026's `worker`
    service consumes this same queue against the same Redis in `docker
    compose up`) — does not require a running worker process."""
    queue = ArqJobQueue(TEST_REDIS_URL)

    await queue.enqueue_generate_embeddings(seeded_document.id)

    pool = await queue._get_pool()
    queued = await pool.queued_jobs()
    assert any(job.function == "generate_embeddings" for job in queued)
