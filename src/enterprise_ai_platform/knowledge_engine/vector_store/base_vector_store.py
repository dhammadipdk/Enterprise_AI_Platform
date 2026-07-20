"""
Base vector store contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from enterprise_ai_platform.knowledge_engine.models import EmbeddedChunk
from enterprise_ai_platform.knowledge_engine.vector_store.vector_store_match import (
    VectorStoreMatch,
)


class BaseVectorStore(ABC):
    """
    Base class for all vector stores.
    """

    @abstractmethod
    def add(self, embedded_chunks: list[EmbeddedChunk]) -> None:
        """
        Add or update embedded chunks in the store.
        """

    @abstractmethod
    def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorStoreMatch]:
        """
        Return the top_k most similar chunks to `vector`.
        """

    @abstractmethod
    def count(self) -> int:
        """
        Return the number of chunks currently stored.
        """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all chunks from the store.
        """