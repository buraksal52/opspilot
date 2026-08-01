import uuid

from app.application.retrieval.context_selection_service import ContextSelectionService
from app.application.retrieval.results import RetrievalResult, RetrievalScores


def _result(content: str, document_title: str = "Doc") -> RetrievalResult:
    return RetrievalResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title=document_title,
        content=content,
        page_number=1,
        section_title=None,
        scores=RetrievalScores(vector=0.5),
    )


def test_select_returns_empty_list_for_empty_input():
    service = ContextSelectionService(token_budget=1000)
    assert service.select([]) == []


def test_select_stops_once_token_budget_is_exceeded():
    # Each ~100-char chunk is ~25 tokens (chars/4 heuristic).
    long_chunk = "word " * 100
    results = [_result(long_chunk) for _ in range(20)]
    service = ContextSelectionService(token_budget=100)

    selected = service.select(results)

    assert 1 <= len(selected) < 20


def test_select_always_keeps_first_candidate_even_if_it_alone_exceeds_budget():
    huge_chunk = "word " * 10_000
    results = [_result(huge_chunk)]
    service = ContextSelectionService(token_budget=10)

    selected = service.select(results)

    assert len(selected) == 1


def test_select_drops_near_duplicate_content():
    base_text = "Standard delivery takes two to four business days for most orders nationwide."
    near_duplicate = base_text + " Extra trailing detail."
    distinct_text = "Refunds are processed within five business days of approval by support staff."

    results = [_result(base_text), _result(near_duplicate), _result(distinct_text)]
    service = ContextSelectionService(token_budget=10_000)

    selected = service.select(results)

    assert len(selected) == 2
    assert selected[0].content == base_text
    assert selected[1].content == distinct_text


def test_select_preserves_input_order():
    topics = [
        "Standard delivery takes two to four business days for most orders.",
        "Refunds are processed within five business days of approval.",
        "Support tickets are triaged by category, priority, and channel.",
        "RapidShip experienced tracking delays during the July migration.",
        "High-value customers receive escalated handling for shipment delays.",
    ]
    results = [_result(text) for text in topics]
    service = ContextSelectionService(token_budget=10_000)

    selected = service.select(results)

    assert [r.content for r in selected] == topics
