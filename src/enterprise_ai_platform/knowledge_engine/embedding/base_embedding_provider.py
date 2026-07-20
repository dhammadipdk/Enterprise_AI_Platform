"""
Base embedding provider contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    """
    Base class for all embedding providers.

    Implementations may be local (no cost, no network dependency once
    the model is cached) or API-based (OpenAI, Cohere, etc.). Callers
    should depend only on this interface, never on a concrete provider,
    so the backend can be swapped without touching calling code.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return a short identifier for this provider, e.g. "local:all-MiniLM-L6-v2".
        """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Return the length of the vectors this provider produces.
        """

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single piece of text.
        """

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts in one call.

        Implementations should batch internally where the backend
        supports it, rather than looping over embed_text.
        """