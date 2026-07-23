"""
Base keyword index contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from enterprise_ai_platform.knowledge_engine.models import Chunk
from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


class BaseKeywordIndex(ABC):
    """
    Base class for all keyword (lexical) indexes.
    """

    @abstractmethod
    def add(self, chunks: list[Chunk]) -> None:
        """
        Add or update chunks in the index.
        """

    @abstractmethod
    def search(
        self,
        repository: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[VectorStoreMatch]:
        """
        Return the top_k chunks most relevant to query_text.
        """

    @abstractmethod
    def count(self) -> int:
        """
        Return the number of chunks currently indexed.
        """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all chunks from the index.
        """