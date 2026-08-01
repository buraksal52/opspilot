import uuid

from app.application.retrieval.hybrid_search_service import HybridSearchService
from app.application.retrieval.results import RetrievalResult, RetrievalScores

WORKSPACE_ID = uuid.uuid4()


def _result(chunk_id: uuid.UUID, *, vector: float | None = None, lexical: float | None = None) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=uuid.uuid4(),
        document_title="Doc",
        content="content",
        page_number=1,
        section_title=None,
        scores=RetrievalScores(vector=vector, lexical=lexical),
    )


class _FakeSearchService:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self._results = results

    async def search(self, *, workspace_id, query, limit):
        return self._results[:limit]


async def test_chunk_found_by_both_retrievers_outranks_single_retriever_hits():
    shared_id, vector_only_id, lexical_only_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    vector_results = [_result(shared_id, vector=0.9), _result(vector_only_id, vector=0.8)]
    lexical_results = [_result(shared_id, lexical=0.5), _result(lexical_only_id, lexical=0.4)]

    service = HybridSearchService(_FakeSearchService(vector_results), _FakeSearchService(lexical_results), candidate_limit=15)
    results = await service.search(workspace_id=WORKSPACE_ID, query="q", limit=10)

    assert results[0].chunk_id == shared_id
    assert results[0].scores.fusion == 2 / 61  # rank 1 in both lists
    assert results[0].scores.vector == 0.9
    assert results[0].scores.lexical == 0.5


async def test_deduplicates_by_chunk_id_into_a_single_result():
    shared_id = uuid.uuid4()
    vector_results = [_result(shared_id, vector=0.9)]
    lexical_results = [_result(shared_id, lexical=0.5)]

    service = HybridSearchService(_FakeSearchService(vector_results), _FakeSearchService(lexical_results), candidate_limit=15)
    results = await service.search(workspace_id=WORKSPACE_ID, query="q", limit=10)

    assert len(results) == 1
    assert results[0].scores.vector == 0.9
    assert results[0].scores.lexical == 0.5


async def test_respects_the_requested_limit():
    results_list = [_result(uuid.uuid4(), vector=1.0 - i * 0.01) for i in range(5)]
    service = HybridSearchService(_FakeSearchService(results_list), _FakeSearchService([]), candidate_limit=15)

    results = await service.search(workspace_id=WORKSPACE_ID, query="q", limit=2)

    assert len(results) == 2


async def test_vector_only_hit_has_no_lexical_score():
    vector_only_id = uuid.uuid4()
    service = HybridSearchService(
        _FakeSearchService([_result(vector_only_id, vector=0.7)]), _FakeSearchService([]), candidate_limit=15
    )

    results = await service.search(workspace_id=WORKSPACE_ID, query="q", limit=10)

    assert results[0].scores.lexical is None
    assert results[0].scores.vector == 0.7
    assert results[0].scores.fusion == 1 / 61
