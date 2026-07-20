"""
Base chunking strategy contract.
"""


from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from enterprise_ai_platform.knowledge_engine.models import Chunk


class BaseChunkingStrategy(ABC):
    """
    Base class for all chunking strategies.
    """

    @abstractmethod
    def chunk(
        self,
        content: Any,
        repository: str,
        domain: str,
        asset: str,
    ) -> list[Chunk]:
        """
        Split asset content into chunks.
        """