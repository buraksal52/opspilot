"""Lexical retrieval (RAG_SYSTEM.md §17, ADR-028, BACKLOG.md 4.5)."""
import uuid

from app.application.retrieval.results import RetrievalResult, RetrievalScores
from app.application.retrieval.vector_search_service import resolve_document_title
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.database.repositories.document_repository import DocumentRepository


class LexicalSearchService:
    def __init__(
        self, document_chunk_repository: DocumentChunkRepository, document_repository: DocumentRepository
    ) -> None:
        self._chunks = document_chunk_repository
        self._documents = document_repository

    async def search(self, *, workspace_id: uuid.UUID, query: str, limit: int) -> list[RetrievalResult]:
        matches = await self._chunks.search_by_text(workspace_id=workspace_id, query=query, limit=limit)

        results: list[RetrievalResult] = []
        title_cache: dict[uuid.UUID, str] = {}
        for chunk, rank in matches:
            title = await resolve_document_title(self._documents, chunk.document_id, title_cache)
            results.append(
                RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=title,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    scores=RetrievalScores(lexical=rank),
                )
            )
        return results
