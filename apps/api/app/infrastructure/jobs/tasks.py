"""arq task definitions.

Each task is a thin wrapper around a plain application-service method
(ADR-024's established pattern) — the actual logic in
`EmbeddingGenerationService` is what tests and the manual evaluation script
call directly, so neither depends on a running worker process (ADR-026).
"""
import logging
import uuid
from typing import Any

from app.application.retrieval.embedding_service import EmbeddingGenerationService
from app.core.config import get_settings
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.embeddings.gemini_provider import GeminiEmbeddingProvider

logger = logging.getLogger(__name__)


async def generate_embeddings(ctx: dict[str, Any], document_id: str) -> None:
    settings = get_settings()
    async with async_session_factory() as session:
        repository = DocumentChunkRepository(session)
        provider = GeminiEmbeddingProvider(
            api_key=settings.gemini_api_key,
            model=settings.embedding_model,
            output_dimension=settings.embedding_dimension,
        )
        service = EmbeddingGenerationService(repository, provider, settings.embedding_model)
        try:
            embedded_count = await service.generate_for_document(uuid.UUID(document_id))
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Embedding generation failed for document %s", document_id)
            raise
        else:
            logger.info("Embedded %d chunk(s) for document %s", embedded_count, document_id)
