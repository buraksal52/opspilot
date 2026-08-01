"""Deterministic in-memory embedding provider used by all automated tests
(TESTING.md §30 — no live paid API calls in normal test runs) and available
for local development without a GEMINI_API_KEY.

Same text always maps to the same vector; different texts map to different
vectors with high probability. This is enough to exercise chunking →
embedding → retrieval plumbing without depending on real semantic quality.
"""
import hashlib
import random

from app.infrastructure.embeddings.base import EmbeddingProvider, EmbeddingTaskType


def _text_to_vector(text: str, dimension: int) -> list[float]:
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(dimension)]


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 768) -> None:
        self._dimension = dimension

    async def embed_batch(self, texts: list[str], *, task_type: EmbeddingTaskType) -> list[list[float]]:
        return [_text_to_vector(text, self._dimension) for text in texts]
