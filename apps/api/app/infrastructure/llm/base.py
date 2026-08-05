"""LLM generation provider abstraction (ARCHITECTURE.md §12, ADR-015, ADR-031).

Two methods only — not the full generate()/generate_structured()/stream()
sketch ARCHITECTURE.md describes conceptually. `stream()` has no caller yet
(ADR-031) and is intentionally omitted until one exists, matching how
`EmbeddingProvider` only ever implemented `embed_batch`.
"""
from typing import Protocol, TypeVar

from pydantic import BaseModel

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class LLMProviderError(Exception):
    """Raised when the underlying provider fails after any safe retries, or
    returns output that does not validate against the requested schema
    (ARCHITECTURE.md §22 — bounded, never silently swallowed)."""


class LLMProvider(Protocol):
    async def generate_structured(self, prompt: str, response_model: type[ResponseModel]) -> ResponseModel:
        """Returns AI output validated against `response_model` (ADR-011).
        Used wherever AI output drives program logic: analysis intent/plan,
        SQL proposals."""
        ...

    async def generate(self, prompt: str) -> str:
        """Returns bounded free-form text. Used only for presentation prose
        that does not drive control flow (ANALYTICS_ENGINE.md §15) — never
        for values a decision depends on."""
        ...
