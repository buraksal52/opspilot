import dataclasses
import uuid

from app.application.retrieval.reranking_service import RerankingService
from app.application.retrieval.results import RetrievalResult, RetrievalScores

WORKSPACE_ID = uuid.uuid4()


def _result(content: str, vector: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title="Doc",
        content=content,
        page_number=1,
        section_title=None,
        scores=RetrievalScores(vector=vector),
    )


class _FakeBaseSearchService:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self._results = results

    async def search(self, *, workspace_id, query, limit):
        return self._results[:limit]


class _FakeReranker:
    """Reverses whatever order the base service returned, to make the effect
    of reranking observable in a test."""

    async def rerank(self, *, query, candidates):
        reversed_candidates = list(reversed(candidates))
        return [
            dataclasses.replace(c, scores=dataclasses.replace(c.scores, rerank=1.0 - i / len(reversed_candidates)))
            for i, c in enumerate(reversed_candidates)
        ]


async def test_reranking_service_applies_reranker_to_base_candidates():
    base_results = [_result("first", vector=0.9), _result("second", vector=0.8)]
    service = RerankingService(_FakeBaseSearchService(base_results), _FakeReranker(), candidate_limit=15)

    results = await service.search(workspace_id=WORKSPACE_ID, query="q", limit=10)

    assert results[0].content == "second"
    assert results[1].content == "first"
    assert all(r.scores.rerank is not None for r in results)


async def test_reranking_service_respects_final_limit():
    base_results = [_result(f"chunk-{i}", vector=1.0 - i * 0.1) for i in range(5)]
    service = RerankingService(_FakeBaseSearchService(base_results), _FakeReranker(), candidate_limit=15)

    results = await service.search(workspace_id=WORKSPACE_ID, query="q", limit=2)

    assert len(results) == 2
