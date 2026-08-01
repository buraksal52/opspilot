"""Hybrid retrieval fusion (RAG_SYSTEM.md §19-21, ADR-029, BACKLOG.md 4.6).

Not the active default retrieval path — per ADR-027/ADR-029, this exists to
be compared against the vector-only baseline (`VectorSearchService`), and is
only adopted if a live evaluation run shows a measured improvement
(RAG_SYSTEM.md §37's gate).
"""
import dataclasses
import uuid

from app.application.retrieval.lexical_search_service import LexicalSearchService
from app.application.retrieval.results import RetrievalResult, RetrievalScores
from app.application.retrieval.vector_search_service import VectorSearchService

# Reciprocal Rank Fusion constant (RAG_SYSTEM.md §20). 60 is RRF's
# original-paper/common-practice default — large enough that a single
# retriever's #1-vs-#2 ordering doesn't dominate the fused score.
_RRF_K = 60


def _reciprocal_rank_scores(results: list[RetrievalResult]) -> dict[uuid.UUID, float]:
    return {result.chunk_id: 1.0 / (_RRF_K + rank) for rank, result in enumerate(results, start=1)}


class HybridSearchService:
    def __init__(
        self,
        vector_search_service: VectorSearchService,
        lexical_search_service: LexicalSearchService,
        candidate_limit: int,
    ) -> None:
        self._vector = vector_search_service
        self._lexical = lexical_search_service
        self._candidate_limit = candidate_limit

    async def search(self, *, workspace_id: uuid.UUID, query: str, limit: int) -> list[RetrievalResult]:
        vector_results = await self._vector.search(workspace_id=workspace_id, query=query, limit=self._candidate_limit)
        lexical_results = await self._lexical.search(workspace_id=workspace_id, query=query, limit=self._candidate_limit)

        vector_rrf = _reciprocal_rank_scores(vector_results)
        lexical_rrf = _reciprocal_rank_scores(lexical_results)

        # Deduplicate by stable chunk ID (RAG_SYSTEM.md §21) — a chunk found
        # by both retrievers appears once, with both underlying scores kept.
        merged: dict[uuid.UUID, RetrievalResult] = {}
        for result in [*vector_results, *lexical_results]:
            if result.chunk_id in merged:
                existing = merged[result.chunk_id]
                merged[result.chunk_id] = dataclasses.replace(
                    existing,
                    scores=RetrievalScores(
                        vector=existing.scores.vector if existing.scores.vector is not None else result.scores.vector,
                        lexical=existing.scores.lexical
                        if existing.scores.lexical is not None
                        else result.scores.lexical,
                    ),
                )
            else:
                merged[result.chunk_id] = result

        fused_results = [
            dataclasses.replace(
                result,
                scores=dataclasses.replace(
                    result.scores, fusion=vector_rrf.get(chunk_id, 0.0) + lexical_rrf.get(chunk_id, 0.0)
                ),
            )
            for chunk_id, result in merged.items()
        ]
        fused_results.sort(key=lambda r: r.scores.fusion, reverse=True)
        return fused_results[:limit]
