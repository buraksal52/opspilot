"""Citation generation and validation (RAG_SYSTEM.md §27-28, BACKLOG.md 4.9).

RAG_SYSTEM.md §27's preferred process: Evidence Objects → the model receives
stable evidence IDs → a generated claim references those IDs → the
application resolves them to UI citations. `DocumentChunk.id` (already a
stable UUID, RAG_SYSTEM.md §26) is the evidence ID; nothing new needs to be
minted for it. This service is the "resolve + validate" step, used once
Phase 6's agent starts producing cited claims — there is no agent yet to
call it, but the retrieval layer's citation contract belongs here regardless
of what calls it.
"""
import uuid
from dataclasses import dataclass

from app.application.retrieval.results import RetrievalResult


class UnsupportedCitationError(Exception):
    """A cited chunk_id was not actually present in the retrieved/selected
    result set for this query (RAG_SYSTEM.md §28: "unsupported citation IDs
    should be rejected"). Raised rather than silently dropped, per
    SECURITY.md §39 ("fail closed")."""


@dataclass(frozen=True, slots=True)
class ResolvedCitation:
    """What a UI citation actually needs (RAG_SYSTEM.md §27's "resolves them
    to UI citations")."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    page_number: int | None
    section_title: str | None
    content: str


class CitationValidationService:
    def validate(
        self, cited_chunk_ids: list[uuid.UUID], retrieved_results: list[RetrievalResult]
    ) -> list[ResolvedCitation]:
        """`retrieved_results` must be exactly the workspace-scoped result
        set actually retrieved for this query (e.g. what a search service
        returned) — a chunk_id's presence there simultaneously proves it (a)
        exists, (b) belongs to this workspace (searches are always
        workspace-scoped, RAG_SYSTEM.md §31/SECURITY.md §4), and (c) was
        actually retrieved, satisfying all three of RAG_SYSTEM.md §28's
        checks in one lookup.

        Raises on the first unsupported ID rather than silently dropping it
        — a model citing evidence it was never given is a correctness bug
        worth surfacing, not hiding.
        """
        by_id = {result.chunk_id: result for result in retrieved_results}
        resolved: list[ResolvedCitation] = []
        for chunk_id in cited_chunk_ids:
            result = by_id.get(chunk_id)
            if result is None:
                raise UnsupportedCitationError(
                    f"Citation references chunk_id {chunk_id}, which was not part of the retrieved evidence set."
                )
            resolved.append(
                ResolvedCitation(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    document_title=result.document_title,
                    page_number=result.page_number,
                    section_title=result.section_title,
                    content=result.content,
                )
            )
        return resolved
