"""
Prompt template.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.prompt_engine.models.prompt_variable import (
    PromptVariable,
)


class PromptTemplate(BaseModel):
    """
    A compiled prompt, produced by PromptCompiler from a
    PromptDefinition. Optimized for rendering and immutable -- unlike
    a PromptDefinition, a PromptTemplate has already been validated
    and has its referenced variables pre-extracted, so the future
    Renderer never needs to re-parse the template text.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    version: str

    user_prompt: str

    system_prompt: str | None = None

    variables: list[PromptVariable] = []

    referenced_variables: list[str] = []

    output_schema: dict[str, Any] | None = None

    metadata: dict[str, Any] = {}