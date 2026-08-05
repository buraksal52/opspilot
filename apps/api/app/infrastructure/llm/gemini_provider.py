"""Gemini generation provider (ADR-031), reusing the google-genai SDK/vendor
relationship already established for embeddings (ADR-025) and reranking
(ADR-030). Structured output uses the same `response_schema` pattern as
`GeminiReranker`; retries only transient failures (ARCHITECTURE.md §22).
"""
import asyncio

from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

from app.infrastructure.llm.base import LLMProviderError, ResponseModel

_MAX_RETRIES = 3
_RETRY_BASE_DELAY_SECONDS = 1.0
_RATE_LIMIT_STATUS_CODE = 429


def _is_transient(exc: APIError) -> bool:
    return isinstance(exc, ServerError) or exc.code == _RATE_LIMIT_STATUS_CODE


class GeminiLLMProvider:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_structured(self, prompt: str, response_model: type[ResponseModel]) -> ResponseModel:
        text = await self._generate_with_retry(
            prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=response_model, temperature=0.0
            ),
        )
        try:
            return response_model.model_validate_json(text)
        except ValueError as exc:
            raise LLMProviderError(f"LLM returned invalid structured output: {exc}") from exc

    async def generate(self, prompt: str) -> str:
        return await self._generate_with_retry(prompt, config=types.GenerateContentConfig(temperature=0.2))

    async def _generate_with_retry(self, prompt: str, *, config: "types.GenerateContentConfig") -> str:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model, contents=prompt, config=config
                )
                if response.text is None:
                    raise LLMProviderError("Gemini returned no text output.")
                return response.text
            except APIError as exc:
                last_error = exc
                if not _is_transient(exc) or attempt == _MAX_RETRIES - 1:
                    raise LLMProviderError(f"Gemini generation request failed: {exc}") from exc
                await asyncio.sleep(_RETRY_BASE_DELAY_SECONDS * (2**attempt))

        raise LLMProviderError(f"Gemini generation request failed: {last_error}") from last_error
