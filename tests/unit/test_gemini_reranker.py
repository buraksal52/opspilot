"""GeminiReranker behavior with the SDK client mocked (TESTING.md §13, §30)."""
import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.genai.errors import ClientError, ServerError

from app.application.retrieval.results import RetrievalResult, RetrievalScores
from app.infrastructure.rerankers.base import RerankerError
from app.infrastructure.rerankers.gemini_reranker import GeminiReranker


def _candidate(content: str) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title="Doc",
        content=content,
        page_number=1,
        section_title=None,
        scores=RetrievalScores(vector=0.5),
    )


def _mock_response(scores: list[dict]) -> MagicMock:
    response = MagicMock()
    response.text = json.dumps({"scores": scores})
    response.usage_metadata = MagicMock(prompt_token_count=10, candidates_token_count=5)
    return response


@pytest.fixture
def reranker():
    return GeminiReranker(api_key="test-key", model="gemini-2.5-flash")


async def test_rerank_orders_candidates_by_relevance_score(reranker):
    candidates = [_candidate("Low relevance."), _candidate("High relevance.")]
    reranker._client.aio.models.generate_content = AsyncMock(
        return_value=_mock_response([{"index": 0, "relevance_score": 0.1}, {"index": 1, "relevance_score": 0.9}])
    )

    results = await reranker.rerank(query="q", candidates=candidates)

    assert results[0].content == "High relevance."
    assert results[0].scores.rerank == 0.9
    assert results[1].scores.rerank == 0.1


async def test_rerank_handles_empty_candidates_without_calling_provider(reranker):
    reranker._client.aio.models.generate_content = AsyncMock()

    results = await reranker.rerank(query="q", candidates=[])

    assert results == []
    reranker._client.aio.models.generate_content.assert_not_called()


async def test_rerank_retries_on_server_error_then_succeeds(reranker):
    candidates = [_candidate("Only candidate.")]
    server_error = ServerError(500, {"error": {"message": "boom"}}, response=None)
    reranker._client.aio.models.generate_content = AsyncMock(
        side_effect=[server_error, _mock_response([{"index": 0, "relevance_score": 0.7}])]
    )

    results = await reranker.rerank(query="q", candidates=candidates)

    assert results[0].scores.rerank == 0.7
    assert reranker._client.aio.models.generate_content.call_count == 2


async def test_rerank_does_not_retry_non_transient_client_error(reranker):
    candidates = [_candidate("Only candidate.")]
    auth_error = ClientError(401, {"error": {"message": "invalid api key"}}, response=None)
    mock = AsyncMock(side_effect=auth_error)
    reranker._client.aio.models.generate_content = mock

    with pytest.raises(RerankerError):
        await reranker.rerank(query="q", candidates=candidates)

    assert mock.call_count == 1


async def test_rerank_raises_on_invalid_structured_output(reranker):
    candidates = [_candidate("Only candidate.")]
    bad_response = MagicMock()
    bad_response.text = "not valid json"
    bad_response.usage_metadata = None
    reranker._client.aio.models.generate_content = AsyncMock(return_value=bad_response)

    with pytest.raises(RerankerError):
        await reranker.rerank(query="q", candidates=candidates)


async def test_rerank_preserves_candidate_when_index_missing_from_response(reranker):
    """A candidate the model didn't score keeps scores.rerank=None and sorts
    below scored candidates, rather than the call failing outright."""
    candidates = [_candidate("Scored."), _candidate("Not scored.")]
    reranker._client.aio.models.generate_content = AsyncMock(
        return_value=_mock_response([{"index": 0, "relevance_score": 0.6}])
    )

    results = await reranker.rerank(query="q", candidates=candidates)

    assert results[0].content == "Scored."
    assert results[1].content == "Not scored."
    assert results[1].scores.rerank is None
