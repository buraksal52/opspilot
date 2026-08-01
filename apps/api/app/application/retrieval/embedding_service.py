"""Embedding generation (RAG_SYSTEM.md §12-14, BACKLOG.md 4.3).

Called directly by the arq task (`app/infrastructure/jobs/tasks.py`) and,
identically, by tests and the manual evaluation script — neither depends on a
running worker process (ADR-026, mirroring the pattern ADR-024 already
established for ingestion).
"""
import uuid

from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.embeddings.base import EmbeddingProvider, EmbeddingTaskType

# Bumped whenever the embedding configuration (model, output dimension, or
# chunking strategy) changes in a way that makes previously stored vectors
# incomparable to newly generated ones (RAG_SYSTEM.md §14).
EMBEDDING_VERSION = "v1"


class EmbeddingGenerationService:
    def __init__(
        self,
        document_chunk_repository: DocumentChunkRepository,
        embedding_provider: EmbeddingProvider,
        model_name: str,
    ) -> None:
        self._chunks = document_chunk_repository
        self._provider = embedding_provider
        self._model_name = model_name

    async def generate_for_document(self, document_id: uuid.UUID) -> int:
        """Embeds every chunk of `document_id` that doesn't have an
        embedding yet. Returns the number of chunks embedded. Safe to call
        repeatedly (e.g. after a partial failure) — already-embedded chunks
        are never re-fetched or re-embedded."""
        chunks = await self._chunks.list_missing_embeddings(document_id)
        if not chunks:
            return 0

        vectors = await self._provider.embed_batch(
            [chunk.content for chunk in chunks], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT
        )
        for chunk, vector in zip(chunks, vectors, strict=True):
            await self._chunks.set_embedding(
                chunk.id, embedding=vector, embedding_model=self._model_name, embedding_version=EMBEDDING_VERSION
            )
        return len(chunks)
