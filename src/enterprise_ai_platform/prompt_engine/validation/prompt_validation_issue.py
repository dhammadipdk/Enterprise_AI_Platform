"""
Prompt validation issue.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class PromptValidationIssue(BaseModel):
    """
    One validation finding for a prompt definition.
    """

    model_config = ConfigDict(frozen=True)

    severity: Literal["error", "warning"]

    code: str

    message: str