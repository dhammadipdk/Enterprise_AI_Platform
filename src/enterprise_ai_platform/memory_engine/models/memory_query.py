"""
Memory query.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.memory_engine.models.memory_type import MemoryType


class MemoryQuery(BaseModel):
    """
    A search request against stored memory items (Section 7).

    V1 supports exact-match filtering only (collection, memory_type,
    owner, metadata key/value equality) -- Section 16's semantic/
    hybrid/temporal/graph-traversal retrieval strategies are a
    deliberately separate, later task, the same staged approach
    Knowledge Engine used (keyword search shipped well before vector
    search and hybrid retrieval).
    """

    model_config = ConfigDict(frozen=True)

    collection: str | None = None

    memory_type: MemoryType | None = None

    owner: str | None = None

    metadata_filter: dict[str, Any] | None = None

    include_expired: bool = False

    limit: int = 10