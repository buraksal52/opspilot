import uuid

from app.application.retrieval.lexical_search_service import LexicalSearchService
from app.domain.data_source import SourceType
from app.domain.document import DocumentType
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.database.repositories.document_repository import DocumentRepository


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


async def test_search_finds_keyword_match_and_resolves_document_title(db_session, seeded_workspace):
    document = await _make_document(db_session, seeded_workspace, "Shipping Policy")
    chunk_repo = DocumentChunkRepository(db_session)
    await chunk_repo.bulk_create(
        workspace_id=seeded_workspace.id,
        document_id=document.id,
        chunks=[
            {
                "chunk_index": 0,
                "content": "Standard delivery takes 2-4 business days.",
                "page_number": 1,
                "section_title": None,
                "token_count": 10,
                "metadata": {},
            }
        ],
    )
    await db_session.commit()

    service = LexicalSearchService(chunk_repo, DocumentRepository(db_session))
    results = await service.search(workspace_id=seeded_workspace.id, query="delivery", limit=5)

    assert len(results) == 1
    assert results[0].document_title == "Shipping Policy"
    assert results[0].scores.lexical is not None
    assert results[0].scores.vector is None
