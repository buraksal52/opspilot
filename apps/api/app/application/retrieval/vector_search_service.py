"""Vector retrieval (RAG_SYSTEM.md §18, §26, BACKLOG.md 4.4).

Vector-only baseline — per RAG_SYSTEM.md §37 ("Baseline First") and the
measured result in ADR-027, this remains the active default retrieval path;
hybrid fusion (BACKLOG.md 4.6) is a separate, explicitly opt-in service.
"""
import uuid

from app.application.retrieval.results import RetrievalResult, RetrievalScores
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.embeddings.base import EmbeddingProvider, EmbeddingTaskType


async def resolve_document_title(
    document_repository: DocumentRepository, document_id: uuid.UUID, cache: dict[uuid.UUID, str]
) -> str:
    """Shared title-resolution helper (vector/lexical/hybrid retrieval all
    need it) with a per-call cache, since a single search's results usually
    reference only a handful of distinct documents."""
    if document_id not in cache:
        document = await document_repository.get_by_id(document_id)
        cache[document_id] = document.title if document else "Unknown document"
    return cache[document_id]


class VectorSearchService:
    def __init__(
        self,
        document_chunk_repository: DocumentChunkRepository,
        document_repository: DocumentRepository,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._chunks = document_chunk_repository
        self._documents = document_repository
        self._embeddings = embedding_provider

    async def search(self, *, workspace_id: uuid.UUID, query: str, limit: int) -> list[RetrievalResult]:
        """Workspace-scoped semantic search (SECURITY.md §4, RAG_SYSTEM.md
        §31 — mandatory isolation, enforced inside the repository query)."""
        query_vectors = await self._embeddings.embed_batch([query], task_type=EmbeddingTaskType.RETRIEVAL_QUERY)
        if not query_vectors:
            return []
        query_vector = query_vectors[0]

        matches = await self._chunks.search_by_embedding(
            workspace_id=workspace_id, query_embedding=query_vector, limit=limit
        )

        results: list[RetrievalResult] = []
        title_cache: dict[uuid.UUID, str] = {}
        for chunk, distance in matches:
            title = await resolve_document_title(self._documents, chunk.document_id, title_cache)
            # pgvector cosine_distance returns 1 - cosine_similarity; report
            # similarity (higher = better) to match RAG_SYSTEM.md §26's
            # scores.vector convention.
            results.append(
                RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=title,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    scores=RetrievalScores(vector=1.0 - distance),
                )
            )
        return results
