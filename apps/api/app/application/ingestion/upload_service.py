"""Upload orchestration (BACKLOG.md 3.2).

Per ADR-024, processing runs synchronously within the upload request: by the
time `upload()` returns, the DataSource is already READY or FAILED — there is
no separate "poll for processing status" step in V1. A ParserError during
ingestion is not a failed HTTP request; it is a successfully recorded
DataSource in FAILED status with `error_message` set, since the upload itself
(receiving and validating the file) succeeded even if parsing did not.
"""
import pathlib
import uuid
from datetime import UTC, datetime

from app.domain.data_source import DataSource, DataSourceStatus, SourceType
from app.application.ingestion.dataset_ingestion_service import DatasetIngestionService
from app.application.ingestion.document_ingestion_service import DocumentIngestionService
from app.application.ingestion.upload_validation import validate_upload
from app.infrastructure.database.repositories.data_source_repository import DataSourceRepository
from app.infrastructure.jobs.queue import JobQueue
from app.infrastructure.parsers.base import ParserError
from app.infrastructure.storage.file_storage import FileStorage

_DEFAULT_MIME_BY_SOURCE_TYPE = {
    SourceType.CSV: "text/csv",
    SourceType.PDF: "application/pdf",
    SourceType.MARKDOWN: "text/markdown",
    SourceType.TEXT: "text/plain",
}


class UploadService:
    def __init__(
        self,
        data_source_repository: DataSourceRepository,
        file_storage: FileStorage,
        document_ingestion_service: DocumentIngestionService,
        dataset_ingestion_service: DatasetIngestionService,
        job_queue: JobQueue,
        max_upload_size_bytes: int,
    ) -> None:
        self._data_sources = data_source_repository
        self._storage = file_storage
        self._documents = document_ingestion_service
        self._datasets = dataset_ingestion_service
        self._job_queue = job_queue
        self._max_upload_size_bytes = max_upload_size_bytes

    async def upload(
        self, *, workspace_id: uuid.UUID, filename: str, content_type: str | None, content: bytes
    ) -> DataSource:
        source_type = validate_upload(
            filename=filename,
            size_bytes=len(content),
            content=content,
            max_size_bytes=self._max_upload_size_bytes,
        )

        extension = pathlib.Path(filename).suffix.lower()
        display_name = pathlib.Path(filename).stem or filename

        data_source_id = uuid.uuid4()
        storage_key = self._storage.save(
            workspace_id=workspace_id, data_source_id=data_source_id, extension=extension, content=content
        )

        data_source = await self._data_sources.create(
            id=data_source_id,
            workspace_id=workspace_id,
            name=display_name,
            source_type=source_type,
            original_filename=filename,
            mime_type=content_type or _DEFAULT_MIME_BY_SOURCE_TYPE[source_type],
            file_size_bytes=len(content),
            storage_key=storage_key,
        )

        await self._data_sources.update_status(data_source.id, status=DataSourceStatus.PROCESSING)

        try:
            if source_type == SourceType.CSV:
                await self._datasets.ingest(
                    workspace_id=workspace_id, data_source_id=data_source.id, name=display_name, content=content
                )
            else:
                document = await self._documents.ingest(
                    workspace_id=workspace_id,
                    data_source_id=data_source.id,
                    source_type=source_type,
                    title=display_name,
                    content=content,
                )
        except ParserError as exc:
            await self._data_sources.update_status(
                data_source.id,
                status=DataSourceStatus.FAILED,
                error_message=str(exc),
                processed_at=datetime.now(UTC),
            )
        else:
            if source_type != SourceType.CSV:
                # Chunks already exist (synchronous, ADR-026); embedding
                # generation is the async part, enqueued here.
                await self._job_queue.enqueue_generate_embeddings(document.id)
            await self._data_sources.update_status(
                data_source.id, status=DataSourceStatus.READY, processed_at=datetime.now(UTC)
            )

        result = await self._data_sources.get_by_id(data_source.id)
        assert result is not None  # just created/updated in this same transaction
        return result
