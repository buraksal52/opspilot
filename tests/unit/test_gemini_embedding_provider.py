"""GeminiEmbeddingProvider error/retry behavior, with the SDK client mocked
(TESTING.md §13, §30 — no live network calls)."""
from unittest.mock import AsyncMock

import pytest
from google.genai import types
from google.genai.errors import ClientError, ServerError

from app.infrastructure.embeddings.base import EmbeddingProviderError, EmbeddingTaskType
from app.infrastructure.embeddings.gemini_provider import GeminiEmbeddingProvider


def _response(vectors: list[list[float]]) -> types.EmbedContentResponse:
    return types.EmbedContentResponse(embeddings=[types.ContentEmbedding(values=v) for v in vectors])


@pytest.fixture
def provider(monkeypatch):
    instance = GeminiEmbeddingProvider(api_key="test-key", model="gemini-embedding-001", output_dimension=8)
    return instance


async def test_embed_batch_returns_vectors_on_success(provider):
    provider._client.aio.models.embed_content = AsyncMock(return_value=_response([[0.1] * 8, [0.2] * 8]))

    vectors = await provider.embed_batch(["a", "b"], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT)

    assert vectors == [[0.1] * 8, [0.2] * 8]


async def test_embed_batch_retries_on_server_error_then_succeeds(provider):
    server_error = ServerError(500, {"error": {"message": "boom"}}, response=None)
    provider._client.aio.models.embed_content = AsyncMock(
        side_effect=[server_error, _response([[0.3] * 8])]
    )

    vectors = await provider.embed_batch(["a"], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT)

    assert vectors == [[0.3] * 8]
    assert provider._client.aio.models.embed_content.call_count == 2


async def test_embed_batch_retries_on_rate_limit_then_succeeds(provider):
    rate_limit_error = ClientError(429, {"error": {"message": "rate limited"}}, response=None)
    provider._client.aio.models.embed_content = AsyncMock(
        side_effect=[rate_limit_error, _response([[0.4] * 8])]
    )

    vectors = await provider.embed_batch(["a"], task_type=EmbeddingTaskType.RETRIEVAL_QUERY)

    assert vectors == [[0.4] * 8]


async def test_embed_batch_does_not_retry_non_transient_client_error(provider):
    auth_error = ClientError(401, {"error": {"message": "invalid api key"}}, response=None)
    mock = AsyncMock(side_effect=auth_error)
    provider._client.aio.models.embed_content = mock

    with pytest.raises(EmbeddingProviderError):
        await provider.embed_batch(["a"], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT)

    assert mock.call_count == 1  # no retry for a permanent/config error


async def test_embed_batch_raises_after_exhausting_retries(provider, monkeypatch):
    import app.infrastructure.embeddings.gemini_provider as module

    monkeypatch.setattr(module, "_RETRY_BASE_DELAY_SECONDS", 0)
    server_error = ServerError(503, {"error": {"message": "unavailable"}}, response=None)
    mock = AsyncMock(side_effect=server_error)
    provider._client.aio.models.embed_content = mock

    with pytest.raises(EmbeddingProviderError):
        await provider.embed_batch(["a"], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT)

    assert mock.call_count == module._MAX_RETRIES


async def test_embed_batch_handles_empty_input_without_calling_provider(provider):
    provider._client.aio.models.embed_content = AsyncMock()

    result = await provider.embed_batch([], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT)

    assert result == []
    provider._client.aio.models.embed_content.assert_not_called()
