"""
Memory item.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai_platform.memory_engine.models.memory_type import MemoryType


class MemoryItem(BaseModel):
    """
    One stored memory record (Section 9).

    `collection` models the frozen spec's separate "MemoryCollection"
    concept (Section 10: groups like Conversation, Workflow, User,
    Agent, ...) as a plain string namespace (e.g.
    "conversation:session123") rather than its own class -- the
    simpler equivalent of how Knowledge Engine used plain
    "repository"/"domain" string keys rather than dedicated objects.

    `version` is a simple integer counter, not the "name@semver"
    pattern used for Prompt/Workflow/Model/Tool definitions -- a
    memory item isn't "the same named thing at a different release"
    the way those are; it's an individual record that gets revised in
    place (see MemoryService.update_metadata).
    """

    model_config = ConfigDict(frozen=True)

    memory_type: MemoryType

    content: Any

    collection: str

    memory_id: str = Field(default_factory=lambda: str(uuid4()))

    embedding: list[float] | None = None

    metadata: dict[str, Any] = {}

    owner: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    expires_at: datetime | None = None

    version: int = 1