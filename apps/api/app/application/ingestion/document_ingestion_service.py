import uuid

from app.application.retrieval.chunking_service import ChunkingService
from app.domain.data_source import SourceType
from app.domain.document import Document, DocumentType
from app.infrastructure.database.repositories.document_chunk_repository import DocumentChunkRepository
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.parsers.markdown_parser import parse_markdown
from app.infrastructure.parsers.pdf_parser import parse_pdf
from app.infrastructure.parsers.text_parser import parse_text

_PARSERS = {
    SourceType.PDF: (DocumentType.PDF, parse_pdf),
    SourceType.MARKDOWN: (DocumentType.MARKDOWN, parse_markdown),
    SourceType.TEXT: (DocumentType.TEXT, parse_text),
}


class DocumentIngestionService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_chunk_repository: DocumentChunkRepository,
        chunking_service: ChunkingService,
    ) -> None:
        self._documents = document_repository
        self._chunks = document_chunk_repository
        self._chunking = chunking_service

    async def ingest(
        self, *, workspace_id: uuid.UUID, data_source_id: uuid.UUID, source_type: SourceType, title: str, content: bytes
    ) -> Document:
        document_type, parse = _PARSERS[source_type]
        parsed = parse(content)

        metadata = dict(parsed.metadata)
        if parsed.pages is not None:
            metadata["pages"] = parsed.pages

        document = await self._documents.create(
            workspace_id=workspace_id,
            data_source_id=data_source_id,
            title=title,
            document_type=document_type,
            text_content=parsed.text,
            page_count=parsed.page_count,
            language=parsed.language,
            metadata=metadata,
        )

        # Chunking is pure CPU work, so it stays synchronous inside ingestion
        # (ADR-026) — only embedding generation (Increment 4) moves to arq.
        chunk_dicts = self._chunking.chunk_document(document)
        if chunk_dicts:
            await self._chunks.bulk_create(workspace_id=workspace_id, document_id=document.id, chunks=chunk_dicts)

        return document
