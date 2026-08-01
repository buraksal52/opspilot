import uuid

import pytest

from app.application.retrieval.citation_service import CitationValidationService, UnsupportedCitationError
from app.application.retrieval.results import RetrievalResult, RetrievalScores


def _result(chunk_id: uuid.UUID | None = None, document_title: str = "Refund Policy") -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id or uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title=document_title,
        content="Refunds are processed within five business days.",
        page_number=2,
        section_title="Delayed Deliveries",
        scores=RetrievalScores(vector=0.8),
    )


def test_validate_resolves_cited_ids_that_were_actually_retrieved():
    retrieved = [_result()]
    chunk_id = retrieved[0].chunk_id
    service = CitationValidationService()

    resolved = service.validate([chunk_id], retrieved)

    assert len(resolved) == 1
    assert resolved[0].chunk_id == chunk_id
    assert resolved[0].document_title == "Refund Policy"
    assert resolved[0].page_number == 2
    assert resolved[0].section_title == "Delayed Deliveries"


def test_validate_rejects_a_chunk_id_that_was_never_retrieved():
    retrieved = [_result()]
    fabricated_id = uuid.uuid4()
    service = CitationValidationService()

    with pytest.raises(UnsupportedCitationError):
        service.validate([fabricated_id], retrieved)


def test_validate_rejects_a_chunk_from_a_different_query_or_workspace():
    """A chunk_id that's real elsewhere but wasn't part of *this* retrieved
    set must still be rejected — presence in the passed-in result set is the
    only source of truth (it's already workspace-scoped by construction)."""
    someone_elses_chunk = _result()
    retrieved_for_this_query = [_result()]
    service = CitationValidationService()

    with pytest.raises(UnsupportedCitationError):
        service.validate([someone_elses_chunk.chunk_id], retrieved_for_this_query)


def test_validate_handles_multiple_valid_citations_in_order():
    retrieved = [_result(document_title="Doc A"), _result(document_title="Doc B")]
    service = CitationValidationService()

    resolved = service.validate([retrieved[1].chunk_id, retrieved[0].chunk_id], retrieved)

    assert [r.document_title for r in resolved] == ["Doc B", "Doc A"]


def test_validate_handles_empty_citation_list():
    service = CitationValidationService()
    assert service.validate([], [_result()]) == []
