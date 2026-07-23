"""
Variable resolution issue.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class VariableResolutionIssue(BaseModel):
    """
    One finding from resolving a template's variables against
    provided values.
    """

    model_config = ConfigDict(frozen=True)

    severity: Literal["error", "warning"]

    code: str

    message: str