"""GeminiLLMProvider behavior with the SDK client mocked (TESTING.md §13, §30)."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.genai.errors import ClientError, ServerError
from pydantic import BaseModel

from app.infrastructure.llm.base import LLMProviderError
from app.infrastructure.llm.gemini_provider import GeminiLLMProvider


class _Answer(BaseModel):
    value: int


def _mock_response(text: str) -> MagicMock:
    response = MagicMock()
    response.text = text
    return response


@pytest.fixture
def provider():
    return GeminiLLMProvider(api_key="test-key", model="gemini-flash-latest")


async def test_generate_structured_validates_against_response_model(provider):
    provider._client.aio.models.generate_content = AsyncMock(return_value=_mock_response('{"value": 42}'))

    result = await provider.generate_structured("prompt", _Answer)

    assert result == _Answer(value=42)


async def test_generate_structured_raises_on_invalid_json(provider):
    provider._client.aio.models.generate_content = AsyncMock(return_value=_mock_response("not json"))

    with pytest.raises(LLMProviderError):
        await provider.generate_structured("prompt", _Answer)


async def test_generate_returns_plain_text(provider):
    provider._client.aio.models.generate_content = AsyncMock(return_value=_mock_response("free-form answer"))

    result = await provider.generate("prompt")

    assert result == "free-form answer"


async def test_retries_on_server_error_then_succeeds(provider):
    server_error = ServerError(500, {"error": {"message": "boom"}}, response=None)
    provider._client.aio.models.generate_content = AsyncMock(
        side_effect=[server_error, _mock_response('{"value": 1}')]
    )

    result = await provider.generate_structured("prompt", _Answer)

    assert result == _Answer(value=1)
    assert provider._client.aio.models.generate_content.call_count == 2


async def test_does_not_retry_non_transient_error(provider):
    auth_error = ClientError(401, {"error": {"message": "invalid api key"}}, response=None)
    mock = AsyncMock(side_effect=auth_error)
    provider._client.aio.models.generate_content = mock

    with pytest.raises(LLMProviderError):
        await provider.generate_structured("prompt", _Answer)

    assert mock.call_count == 1
