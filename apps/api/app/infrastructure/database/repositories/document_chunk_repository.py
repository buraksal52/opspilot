import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.document_chunk import DocumentChunk
from app.infrastructure.database.models.document_chunk import DocumentChunkModel


def _to_domain(model: DocumentChunkModel) -> DocumentChunk:
    return DocumentChunk(
        id=model.id,
        workspace_id=model.workspace_id,
        document_id=model.document_id,
        chunk_index=model.chunk_index,
        content=model.content,
        page_number=model.page_number,
        section_title=model.section_title,
        token_count=model.token_count,
        embedding=list(model.embedding) if model.embedding is not None else None,
        embedding_model=model.embedding_model,
        embedding_version=model.embedding_version,
        metadata=model.chunk_metadata,
        created_at=model.created_at,
    )


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(
        self,
        *,
        workspace_id: uuid.UUID,
        document_id: uuid.UUID,
        chunks: list[dict],
    ) -> list[DocumentChunk]:
        """Persists chunks produced by the chunking service (embeddings not
        yet computed — RAG_SYSTEM.md §4 "Chunk" precedes "Embed"). Each dict
        must have: chunk_index, content, page_number, section_title,
        token_count, metadata."""
        models = [
            DocumentChunkModel(
                workspace_id=workspace_id,
                document_id=document_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                page_number=chunk["page_number"],
                section_title=chunk["section_title"],
                token_count=chunk["token_count"],
                chunk_metadata=chunk.get("metadata", {}),
            )
            for chunk in chunks
        ]
        self._session.add_all(models)
        await self._session.flush()
        for model in models:
            await self._session.refresh(model)
        return [_to_domain(model) for model in models]

    async def list_by_document(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        result = await self._session.execute(
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index)
        )
        return [_to_domain(model) for model in result.scalars().all()]

    async def list_missing_embeddings(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        result = await self._session.execute(
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .where(DocumentChunkModel.embedding.is_(None))
            .order_by(DocumentChunkModel.chunk_index)
        )
        return [_to_domain(model) for model in result.scalars().all()]

    async def set_embedding(
        self, chunk_id: uuid.UUID, *, embedding: list[float], embedding_model: str, embedding_version: str
    ) -> None:
        model = await self._session.get(DocumentChunkModel, chunk_id)
        if model is None:
            return
        model.embedding = embedding
        model.embedding_model = embedding_model
        model.embedding_version = embedding_version
        await self._session.flush()

    async def search_by_embedding(
        self, *, workspace_id: uuid.UUID, query_embedding: list[float], limit: int
    ) -> list[tuple[DocumentChunk, float]]:
        """Workspace-scoped cosine-distance nearest-neighbor search
        (RAG_SYSTEM.md §18, §31; SECURITY.md §4 — mandatory workspace
        isolation). Plain sequential scan, no ANN index yet: at Northstar's
        corpus size exact search is acceptable (RAG_SYSTEM.md §18)."""
        distance = DocumentChunkModel.embedding.cosine_distance(query_embedding)
        result = await self._session.execute(
            select(DocumentChunkModel, distance.label("distance"))
            .where(DocumentChunkModel.workspace_id == workspace_id)
            .where(DocumentChunkModel.embedding.is_not(None))
            .order_by(distance)
            .limit(limit)
        )
        return [(_to_domain(model), float(dist)) for model, dist in result.all()]

    async def search_by_text(
        self, *, workspace_id: uuid.UUID, query: str, limit: int
    ) -> list[tuple[DocumentChunk, float]]:
        """Workspace-scoped PostgreSQL full-text search (ADR-028). Uses
        `websearch_to_tsquery` so ordinary business-question phrasing (not a
        special query syntax) is accepted. Rows that don't match at all are
        excluded by the `@@` predicate, not merely ranked last."""
        tsquery = func.websearch_to_tsquery("english", query)
        rank = func.ts_rank(DocumentChunkModel.content_tsv, tsquery).label("rank")
        result = await self._session.execute(
            select(DocumentChunkModel, rank)
            .where(DocumentChunkModel.workspace_id == workspace_id)
            .where(DocumentChunkModel.content_tsv.op("@@")(tsquery))
            .order_by(rank.desc())
            .limit(limit)
        )
        return [(_to_domain(model), float(rank_value)) for model, rank_value in result.all()]
