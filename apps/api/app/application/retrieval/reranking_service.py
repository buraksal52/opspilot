"""Reranking wraps any base search service's candidates with a rerank pass
(RAG_SYSTEM.md §22, ADR-030, BACKLOG.md 4.7).

Not the active default retrieval path — like hybrid fusion (ADR-029), this
exists to be compared against the current best baseline before being kept
(RAG_SYSTEM.md §37's gate).
"""
import uuid
from typing import Protocol

from app.application.retrieval.results import RetrievalResult
from app.infrastructure.rerankers.base import Reranker


class BaseSearchService(Protocol):
    async def search(self, *, workspace_id: uuid.UUID, query: str, limit: int) -> list[RetrievalResult]: ...


class RerankingService:
    def __init__(self, base_search_service: BaseSearchService, reranker: Reranker, candidate_limit: int) -> None:
        self._base = base_search_service
        self._reranker = reranker
        self._candidate_limit = candidate_limit

    async def search(self, *, workspace_id: uuid.UUID, query: str, limit: int) -> list[RetrievalResult]:
        candidates = await self._base.search(workspace_id=workspace_id, query=query, limit=self._candidate_limit)
        reranked = await self._reranker.rerank(query=query, candidates=candidates)
        return reranked[:limit]
