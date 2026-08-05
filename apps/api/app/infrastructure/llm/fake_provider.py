"""Deterministic, scripted LLM provider used by all automated tests
(TESTING.md §30 — no live paid API calls in normal test runs) and available
for local development without a GEMINI_API_KEY.

Unlike `FakeEmbeddingProvider` (a pure function of its input), structured
generation output cannot be meaningfully derived from the prompt text alone,
so callers script exact responses upfront and the fake returns them in call
order, one per matching `response_model` type.
"""
from collections import defaultdict
from typing import Any

from pydantic import BaseModel

from app.infrastructure.llm.base import LLMProviderError, ResponseModel


class FakeLLMProvider:
    def __init__(self) -> None:
        self._structured_queues: dict[type[BaseModel], list[Any]] = defaultdict(list)
        self._text_queue: list[str] = []
        self.structured_calls: list[tuple[str, type[BaseModel]]] = []
        self.text_calls: list[str] = []

    def queue_structured(self, response: BaseModel) -> None:
        self._structured_queues[type(response)].append(response)

    def queue_text(self, response: str) -> None:
        self._text_queue.append(response)

    async def generate_structured(self, prompt: str, response_model: type[ResponseModel]) -> ResponseModel:
        self.structured_calls.append((prompt, response_model))
        queue = self._structured_queues[response_model]
        if not queue:
            raise LLMProviderError(f"FakeLLMProvider has no queued response for {response_model.__name__}.")
        return queue.pop(0)

    async def generate(self, prompt: str) -> str:
        self.text_calls.append(prompt)
        if not self._text_queue:
            raise LLMProviderError("FakeLLMProvider has no queued text response.")
        return self._text_queue.pop(0)
