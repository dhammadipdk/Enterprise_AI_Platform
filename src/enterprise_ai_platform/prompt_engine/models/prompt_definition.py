"""
Prompt definition.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.prompt_engine.models.prompt_variable import (
    PromptVariable,
)


class PromptDefinition(BaseModel):
    """
    A prompt treated as a versioned software artifact rather than
    plain text -- the raw, as-authored definition, before compilation
    into a PromptTemplate (a later Prompt Engine step).
    """

    model_config = ConfigDict(frozen=True)

    name: str

    version: str

    user_prompt: str

    description: str | None = None

    system_prompt: str | None = None

    variables: list[PromptVariable] = []

    output_schema: dict[str, Any] | None = None

    metadata: dict[str, Any] = {}