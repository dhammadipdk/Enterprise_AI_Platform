"""
Prompt instance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai_platform.prompt_engine.models.prompt_template import (
    PromptTemplate,
)


class PromptInstance(BaseModel):
    """
    Represents one rendered prompt -- the immutable result of running
    a PromptTemplate through PromptRenderer with a set of resolved
    variable values.

    Design note: the frozen spec (Section 12) names a single
    "rendered_prompt" field, but this splits it into
    rendered_system_prompt / rendered_user_prompt instead. Every
    provider Section 22 requires supporting (OpenAI, Anthropic,
    Google, ...) sends system and user content as separate message
    roles, so keeping them separate here is what the eventual Model
    Engine will actually need -- a single combined string would just
    have to be split apart again downstream.
    """

    model_config = ConfigDict(frozen=True)

    template: PromptTemplate

    resolved_variables: dict[str, Any]

    rendered_user_prompt: str

    rendered_system_prompt: str | None = None

    context: dict[str, Any] | None = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )