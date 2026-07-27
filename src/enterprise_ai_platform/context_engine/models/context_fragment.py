"""
Context fragment.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai_platform.context_engine.models.context_category import (
    ContextCategory,
)
from enterprise_ai_platform.context_engine.models.context_source import (
    ContextSource,
)


class ContextFragment(BaseModel):
    """
    One logical contribution to a PlatformContext (Section 10) --
    e.g. retrieved documents, a conversation summary, current workflow
    variables, a user profile.

    `priority` resolves conflicts when two fragments claim the same
    (category, label): the higher-priority fragment wins, and among
    equal priorities, the one that appears later in the input list to
    ContextBuilder.build() wins (see its docstring).
    """

    model_config = ConfigDict(frozen=True)

    source: ContextSource

    category: ContextCategory

    label: str

    content: Any

    fragment_id: str = Field(default_factory=lambda: str(uuid4()))

    priority: int = 0

    metadata: dict[str, Any] = {}