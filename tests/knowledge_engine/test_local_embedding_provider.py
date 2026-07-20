"""
These tests load a real sentence-transformers model. The first run in
a fresh environment downloads the model (roughly 80MB); every run after
that uses the local cache and stays fast.
"""

from enterprise_ai_platform.knowledge_engine.embedding import (
    LocalEmbeddingProvider,
)


def test_local_embedding_provider_returns_correct_dimension() -> None:

    provider = LocalEmbeddingProvider()

    vector = provider.embed_text("Zero depreciation cover")

    assert len(vector) == provider.dimension


def test_local_embedding_provider_batches_correctly() -> None:

    provider = LocalEmbeddingProvider()

    vectors = provider.embed_batch(
        [
            "Zero depreciation cover",
            "No claim bonus",
        ]
    )

    assert len(vectors) == 2

    assert len(vectors[0]) == provider.dimension

    assert vectors[0] != vectors[1]


def test_local_embedding_provider_empty_batch_returns_empty_list() -> None:

    provider = LocalEmbeddingProvider()

    assert provider.embed_batch([]) == []