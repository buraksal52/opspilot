"""Shared retrieval result schema (RAG_SYSTEM.md §26).

Used by every retrieval stage (vector-only, lexical-only, fused, and later
reranked) so a single result shape can flow through the whole pipeline
without callers needing to know which stage produced it.
"""
import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievalScores:
    vector: float | None = None
    lexical: float | None = None
    fusion: float | None = None
    rerank: float | None = None


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Evidence-shaped retrieval output (RAG_SYSTEM.md §26) — not yet a
    persisted Evidence row (that requires an Investigation, Phase 6/8)."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    content: str
    page_number: int | None
    section_title: str | None
    scores: RetrievalScores
