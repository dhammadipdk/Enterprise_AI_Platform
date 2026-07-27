"""
Memory result.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.memory_engine.models.memory_item import (
    MemoryItem,
)


class MemoryResult(BaseModel):
    """
    One match from a memory search (Section 7).

    `score` stays None for V1's exact-match filtering (there's no
    ranking signal yet to compute it from); it becomes meaningful once
    semantic search is added in a later task.
    """

    model_config = ConfigDict(frozen=True)

    item: MemoryItem

    score: float | None = None