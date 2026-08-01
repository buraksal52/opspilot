"""Google Gemini embedding provider (ADR-025).

Batches requests (bounded batch size) and retries only transient failures —
server errors and rate limiting — never validation/auth errors (ARCHITECTURE.md
§22: "retry only operations where retrying is safe").
"""
import asyncio

from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

from app.infrastructure.embeddings.base import EmbeddingProvider, EmbeddingProviderError, EmbeddingTaskType

_MAX_BATCH_SIZE = 32
_MAX_RETRIES = 3
_RETRY_BASE_DELAY_SECONDS = 1.0
_RATE_LIMIT_STATUS_CODE = 429


def _is_transient(exc: APIError) -> bool:
    return isinstance(exc, ServerError) or exc.code == _RATE_LIMIT_STATUS_CODE


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, api_key: str, model: str, output_dimension: int) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._output_dimension = output_dimension

    async def embed_batch(self, texts: list[str], *, task_type: EmbeddingTaskType) -> list[list[float]]:
        if not texts:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(texts), _MAX_BATCH_SIZE):
            batch = texts[start : start + _MAX_BATCH_SIZE]
            vectors.extend(await self._embed_batch_with_retry(batch, task_type))
        return vectors

    async def _embed_batch_with_retry(self, batch: list[str], task_type: EmbeddingTaskType) -> list[list[float]]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.aio.models.embed_content(
                    model=self._model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type.value, output_dimensionality=self._output_dimension
                    ),
                )
                if response.embeddings is None:
                    raise EmbeddingProviderError("Gemini returned no embeddings for a non-empty batch.")
                return [list(embedding.values or []) for embedding in response.embeddings]
            except APIError as exc:
                last_error = exc
                if not _is_transient(exc) or attempt == _MAX_RETRIES - 1:
                    raise EmbeddingProviderError(f"Gemini embedding request failed: {exc}") from exc
                await asyncio.sleep(_RETRY_BASE_DELAY_SECONDS * (2**attempt))

        # Unreachable in practice (the loop always returns or raises above),
        # but keeps type checkers honest about the function's return type.
        raise EmbeddingProviderError(f"Gemini embedding request failed: {last_error}") from last_error
