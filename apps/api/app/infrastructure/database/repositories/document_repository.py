import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.document import Document, DocumentType
from app.infrastructure.database.models.document import DocumentModel


def _to_domain(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        workspace_id=model.workspace_id,
        data_source_id=model.data_source_id,
        title=model.title,
        document_type=DocumentType(model.document_type),
        text_content=model.text_content,
        page_count=model.page_count,
        language=model.language,
        metadata=model.doc_metadata,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        model = await self._session.get(DocumentModel, document_id)
        return _to_domain(model) if model else None

    async def get_by_data_source_id(self, data_source_id: uuid.UUID) -> Document | None:
        from sqlalchemy import select

        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.data_source_id == data_source_id)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        data_source_id: uuid.UUID,
        title: str,
        document_type: DocumentType,
        text_content: str,
        page_count: int | None,
        language: str | None,
        metadata: dict,
    ) -> Document:
        model = DocumentModel(
            workspace_id=workspace_id,
            data_source_id=data_source_id,
            title=title,
            document_type=document_type.value,
            text_content=text_content,
            page_count=page_count,
            language=language,
            doc_metadata=metadata,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)
