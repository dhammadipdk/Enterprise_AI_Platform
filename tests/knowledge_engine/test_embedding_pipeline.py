from enterprise_ai_platform.knowledge_engine import Chunk
from enterprise_ai_platform.knowledge_engine.embedding import (
    BaseEmbeddingProvider,
    EmbeddingPipeline,
)


class _FakeEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic, dependency-free provider used for fast unit tests.
    """

    @property
    def name(self) -> str:
        return "fake"

    @property
    def dimension(self) -> int:
        return 2

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 0.0] for text in texts]


def test_embed_empty_chunk_list_returns_empty_list() -> None:

    pipeline = EmbeddingPipeline(_FakeEmbeddingProvider())

    assert pipeline.embed([]) == []


def test_embed_produces_one_embedded_chunk_per_chunk() -> None:

    chunks = [
        Chunk(
            content="hello",
            repository="insurance",
            domain="policy",
            asset="README",
            chunk_index=0,
        ),
        Chunk(
            content="hi",
            repository="insurance",
            domain="policy",
            asset="README",
            chunk_index=1,
        ),
    ]

    pipeline = EmbeddingPipeline(_FakeEmbeddingProvider())

    embedded = pipeline.embed(chunks)

    assert len(embedded) == 2

    assert embedded[0].vector == [5.0, 0.0]

    assert embedded[1].vector == [2.0, 0.0]

    assert embedded[0].provider == "fake"

    assert embedded[0].chunk == chunks[0]


def test_pipeline_exposes_active_provider() -> None:

    provider = _FakeEmbeddingProvider()

    pipeline = EmbeddingPipeline(provider)

    assert pipeline.provider is provider