"""Context selection (RAG_SYSTEM.md §24-25, BACKLOG.md 4.8).

The highest-ranked chunks are not automatically all passed to the model.
This stage filters an already-ranked result list down to a token-bounded,
deduplicated, diversity-preferring subset — it never reorders or adds
candidates, only drops some.
"""
from app.application.retrieval.chunking_service import estimate_token_count
from app.application.retrieval.results import RetrievalResult

# Word-overlap (Jaccard) threshold above which two chunks are treated as
# expressing the same information (RAG_SYSTEM.md §24: "prefer evidence
# diversity when several chunks express the same information").
_REDUNDANCY_THRESHOLD = 0.8


def _word_set(text: str) -> set[str]:
    return set(text.lower().split())


def _is_redundant(candidate: RetrievalResult, already_selected: list[RetrievalResult]) -> bool:
    candidate_words = _word_set(candidate.content)
    if not candidate_words:
        return False
    for existing in already_selected:
        existing_words = _word_set(existing.content)
        if not existing_words:
            continue
        overlap = len(candidate_words & existing_words) / len(candidate_words | existing_words)
        if overlap >= _REDUNDANCY_THRESHOLD:
            return True
    return False


class ContextSelectionService:
    def __init__(self, token_budget: int) -> None:
        self._token_budget = token_budget

    def select(self, ranked_results: list[RetrievalResult]) -> list[RetrievalResult]:
        """`ranked_results` must already be in relevance order (best first).
        Returns the prefix that fits the token budget, skipping any
        candidate redundant with one already selected. The first candidate
        is always kept even if it alone exceeds the budget — an empty
        context is worse than a single over-budget one (RAG_SYSTEM.md §29/§30
        expects the agent to reason over *something*, not silently nothing)."""
        selected: list[RetrievalResult] = []
        used_tokens = 0
        for candidate in ranked_results:
            if _is_redundant(candidate, selected):
                continue
            candidate_tokens = estimate_token_count(candidate.content)
            if selected and used_tokens + candidate_tokens > self._token_budget:
                break
            selected.append(candidate)
            used_tokens += candidate_tokens
        return selected
