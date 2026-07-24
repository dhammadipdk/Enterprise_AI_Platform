"""
Tool validation issue.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ToolValidationIssue(BaseModel):
    """
    One validation finding for a tool execution request.
    """

    model_config = ConfigDict(frozen=True)

    severity: Literal["error", "warning"]

    code: str

    message: str