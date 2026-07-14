"""
Generic registry implementation.
"""

from __future__ import annotations

from typing import Dict, Generic, List, TypeVar


T = TypeVar("T")


class BaseRegistry(Generic[T]):
    """
    Generic runtime registry.
    """

    def __init__(self) -> None:
        self._items: Dict[str, T] = {}

    def register(self, name: str, item: T) -> None:
        """
        Register an item.
        """

        if name in self._items:
            raise ValueError(f"'{name}' is already registered.")

        self._items[name] = item

    def unregister(self, name: str) -> None:
        """
        Remove an item.
        """

        self._items.pop(name, None)

    def get(self, name: str) -> T:
        """
        Retrieve a registered item.
        """

        if name not in self._items:
            raise KeyError(
                f"No item registered with name '{name}'."
            )

        return self._items[name]

    def exists(self, name: str) -> bool:
        """
        Check if an item exists.
        """

        return name in self._items

    def names(self) -> List[str]:
        """
        Return all registered names.
        """

        return sorted(self._items.keys())

    def clear(self) -> None:
        """
        Remove all registered items.
        """

        self._items.clear()