"""
Embedding pipeline.
"""

from __future__ import annotations

from enterprise_ai_platform.knowledge_engine.embedding.base_embedding_provider import (
    BaseEmbeddingProvider,
)
from enterprise_ai_platform.knowledge_engine.models import Chunk, EmbeddedChunk


class EmbeddingPipeline:
    """
    Converts chunks into embedded chunks using a configured provider.
    """

    def __init__(self, provider: BaseEmbeddingProvider) -> None:

        self._provider = provider

    @property
    def provider(self) -> BaseEmbeddingProvider:
        """
        Return the active embedding provider.
        """

        return self._provider

    def embed(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        """
        Embed a list of chunks in a single batched call.
        """

        if not chunks:
            return []

        vectors = self._provider.embed_batch(
            [chunk.content for chunk in chunks]
        )

        return [
            EmbeddedChunk(
                chunk=chunk,
                vector=vector,
                provider=self._provider.name,
            )
            for chunk, vector in zip(chunks, vectors)
        ]