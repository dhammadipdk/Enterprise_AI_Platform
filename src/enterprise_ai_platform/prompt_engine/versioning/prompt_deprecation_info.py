"""
Prompt deprecation info.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class PromptDeprecationInfo(BaseModel):
    """
    Records that a specific prompt version has been deprecated.

    Deprecation is tracked as registry-level lifecycle state, not as a
    field on PromptTemplate itself -- a compiled template describes
    what a prompt *is*, while whether a given version is still
    recommended for use is a separate, later decision (e.g. a
    regulatory change might deprecate a prompt without its content
    ever changing), so it doesn't belong baked into the immutable
    compiled artifact.
    """

    model_config = ConfigDict(frozen=True)

    reason: str | None = None

    deprecated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )