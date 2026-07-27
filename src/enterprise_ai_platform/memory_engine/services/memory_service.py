"""
Memory service.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)
from enterprise_ai_platform.memory_engine.models import (
    MemoryItem,
    MemoryQuery,
    MemoryResult,
    MemoryType,
)


class MemoryService(BaseService):
    """
    Public API of the Memory Engine (frozen spec, Section 15).

    Implemented in this task: store, retrieve, search,
    update_metadata, archive, delete, statistics, health.

    In-memory storage only for now (a plain dict), matching how every
    other engine in this platform started with the simplest possible
    backend before anything persistent or pluggable was needed
    (ChromaVectorStore's ephemeral default, PromptService's dict-based
    registries) -- a persistent MemoryStore backend is a natural,
    separate future task once one is actually needed.

    Deliberately not implemented yet:
      - Semantic/hybrid/temporal/graph-traversal search (Section 16)
        -- MemoryQuery supports exact-match filtering only for now;
        see its docstring for the reasoning (same staged approach
        Knowledge Engine used).
      - Memory consolidation (Section 14: summarization, aggregation,
        promotion) -- meaningful once there's enough real memory
        volume to consolidate.
      - Policy enforcement beyond expiration (Section 12: retention,
        compression, encryption, replication) -- these matter once
        there's a real persistent backend and real governance
        requirements driving them.
    """

    def __init__(self) -> None:

        super().__init__(name="memory_service")

        self._items: dict[str, MemoryItem] = {}

        self._archived: set[str] = set()

    def initialize(self) -> None:
        """
        Initialize the service.
        """

        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        """
        Start the service.
        """

        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        """
        Stop the service.
        """

        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        """
        Dispose the service and clear all stored memory.
        """

        self._items.clear()

        self._archived.clear()

        self._set_state(ComponentState.DISPOSED)

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def store(
        self,
        memory_type: MemoryType,
        content: Any,
        collection: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
        owner: str | None = None,
        expires_at: datetime | None = None,
    ) -> MemoryItem:
        """
        Store a new memory item and return it.
        """

        item = MemoryItem(
            memory_type=memory_type,
            content=content,
            collection=collection,
            embedding=embedding,
            metadata=metadata or {},
            owner=owner,
            expires_at=expires_at,
        )

        self._items[item.memory_id] = item

        return item

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, memory_id: str) -> MemoryItem:
        """
        Return a single memory item by id.

        Raises KeyError if it doesn't exist or has expired.
        """

        if memory_id not in self._items:
            raise KeyError(f"No memory item with id '{memory_id}'.")

        item = self._items[memory_id]

        if self._is_expired(item):
            raise KeyError(
                f"Memory item '{memory_id}' has expired "
                f"(expired at {item.expires_at})."
            )

        return item

    def search(self, query: MemoryQuery) -> list[MemoryResult]:
        """
        Search stored memory items matching `query`, most recently
        created first.
        """

        matches: list[MemoryItem] = []

        for item in self._items.values():

            if item.memory_id in self._archived:
                continue

            if not query.include_expired and self._is_expired(item):
                continue

            if query.collection is not None and (
                item.collection != query.collection
            ):
                continue

            if query.memory_type is not None and (
                item.memory_type != query.memory_type
            ):
                continue

            if query.owner is not None and item.owner != query.owner:
                continue

            if not self._matches_metadata_filter(
                item.metadata,
                query.metadata_filter,
            ):
                continue

            matches.append(item)

        matches.sort(key=lambda candidate: candidate.created_at, reverse=True)

        return [
            MemoryResult(item=item) for item in matches[: query.limit]
        ]

    def list_collections(self) -> list[str]:
        """
        Return every distinct collection currently in use.
        """

        return sorted({item.collection for item in self._items.values()})

    # ------------------------------------------------------------------
    # Update / lifecycle
    # ------------------------------------------------------------------

    def update_metadata(
        self,
        memory_id: str,
        metadata_updates: dict[str, Any],
    ) -> MemoryItem:
        """
        Merge `metadata_updates` into an existing item's metadata,
        incrementing its version, and return the updated item.
        """

        item = self.retrieve(memory_id)

        updated = MemoryItem(
            memory_id=item.memory_id,
            memory_type=item.memory_type,
            content=item.content,
            collection=item.collection,
            embedding=item.embedding,
            metadata={**item.metadata, **metadata_updates},
            owner=item.owner,
            created_at=item.created_at,
            expires_at=item.expires_at,
            version=item.version + 1,
        )

        self._items[memory_id] = updated

        return updated

    def archive(self, memory_id: str) -> None:
        """
        Archive a memory item. Archived items are excluded from
        search() but remain retrievable via retrieve().
        """

        self.retrieve(memory_id)

        self._archived.add(memory_id)

    def is_archived(self, memory_id: str) -> bool:
        """
        Return True if the memory item is archived.
        """

        return memory_id in self._archived

    def delete(self, memory_id: str) -> None:
        """
        Permanently delete a memory item.
        """

        if memory_id not in self._items:
            raise KeyError(f"No memory item with id '{memory_id}'.")

        del self._items[memory_id]

        self._archived.discard(memory_id)

    # ------------------------------------------------------------------
    # Statistics / health
    # ------------------------------------------------------------------

    def statistics(self) -> dict[str, Any]:
        """
        Return summary statistics about stored memory.
        """

        by_type: dict[str, int] = {}

        for item in self._items.values():
            by_type[item.memory_type.value] = (
                by_type.get(item.memory_type.value, 0) + 1
            )

        return {
            "total_items": len(self._items),
            "archived_items": len(self._archived),
            "collections": len(self.list_collections()),
            "by_type": by_type,
        }

    def health(self) -> bool:
        """
        Return True if the memory store is available.

        Always True for the in-memory backend; meaningful once a real
        persistent backend exists to check.
        """

        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_expired(item: MemoryItem) -> bool:

        if item.expires_at is None:
            return False

        return datetime.now(timezone.utc) >= item.expires_at

    @staticmethod
    def _matches_metadata_filter(
        item_metadata: dict[str, Any],
        metadata_filter: dict[str, Any] | None,
    ) -> bool:

        if not metadata_filter:
            return True

        return all(
            item_metadata.get(key) == value
            for key, value in metadata_filter.items()
        )