"""
Prompt variable.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class PromptVariable(BaseModel):
    """
    Describes one variable a prompt template expects at render time.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    type: str

    required: bool = True

    default_value: Any | None = None

    validation_rules: dict[str, Any] = {}

    description: str | None = None