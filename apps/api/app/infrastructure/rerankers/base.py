"""Reranker abstraction (RAG_SYSTEM.md §22-23, ADR-030, BACKLOG.md 4.7)."""
from typing import Protocol

from app.application.retrieval.results import RetrievalResult


class RerankerError(Exception):
    """Raised when the reranker fails after any safe retries. Never silently
    swallowed — a failed reranking call should surface, not pretend to
    succeed with unranked input (RAG_SYSTEM.md §42)."""


class Reranker(Protocol):
    async def rerank(self, *, query: str, candidates: list[RetrievalResult]) -> list[RetrievalResult]:
        """Returns `candidates` re-ordered by relevance, each with
        `scores.rerank` populated. Must not add or remove candidates."""
        ...
