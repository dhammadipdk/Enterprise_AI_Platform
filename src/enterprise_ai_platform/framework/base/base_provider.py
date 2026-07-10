"""
Base provider contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseProvider(ABC, Generic[T]):
    """
    Base class for all data providers.
    """

    @abstractmethod
    def load(self) -> T:
        """
        Load data.
        """

    @abstractmethod
    def save(self, data: T) -> None:
        """
        Persist data.
        """