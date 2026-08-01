"""Contract tests for EmbeddingProvider implementations (TESTING.md §13).

Runs against FakeEmbeddingProvider only — no live paid API calls in normal
test runs (TESTING.md §30). GeminiEmbeddingProvider's own error/retry
behavior is covered separately in test_gemini_embedding_provider.py using a
mocked client.
"""
from app.infrastructure.embeddings.base import EmbeddingTaskType
from app.infrastructure.embeddings.fake_provider import FakeEmbeddingProvider


async def test_embed_batch_returns_one_vector_per_input_in_order():
    provider = FakeEmbeddingProvider(dimension=16)

    vectors = await provider.embed_batch(["alpha", "beta", "gamma"], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT)

    assert len(vectors) == 3
    assert all(len(v) == 16 for v in vectors)


async def test_embed_batch_handles_empty_input():
    provider = FakeEmbeddingProvider(dimension=16)

    assert await provider.embed_batch([], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT) == []


async def test_embed_batch_is_deterministic_for_the_same_text():
    provider = FakeEmbeddingProvider(dimension=16)

    first = await provider.embed_batch(["same text"], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT)
    second = await provider.embed_batch(["same text"], task_type=EmbeddingTaskType.RETRIEVAL_QUERY)

    assert first == second


async def test_embed_batch_differs_for_different_text():
    provider = FakeEmbeddingProvider(dimension=16)

    vectors = await provider.embed_batch(["alpha", "beta"], task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT)

    assert vectors[0] != vectors[1]
