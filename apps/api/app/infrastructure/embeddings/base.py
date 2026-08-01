"""Embedding provider abstraction (RAG_SYSTEM.md §12, ADR-015, ADR-025).

Application/domain code must depend only on this narrow interface, never on a
specific vendor SDK, so switching providers does not require rewriting
callers (ADR-015).
"""
from enum import StrEnum
from typing import Protocol


class EmbeddingTaskType(StrEnum):
    """Distinguishes how a text will be used, so asymmetric embedding models
    (ADR-025) can embed a chunk and a query differently while callers still
    go through one interface."""

    RETRIEVAL_DOCUMENT = "RETRIEVAL_DOCUMENT"
    RETRIEVAL_QUERY = "RETRIEVAL_QUERY"


class EmbeddingProviderError(Exception):
    """Raised when the underlying provider fails after any safe retries
    (RAG_SYSTEM.md §42, ARCHITECTURE.md §22 — bounded, not silent)."""


class EmbeddingProvider(Protocol):
    async def embed_batch(self, texts: list[str], *, task_type: EmbeddingTaskType) -> list[list[float]]:
        """Returns one embedding vector per input text, same order as `texts`."""
        ...
