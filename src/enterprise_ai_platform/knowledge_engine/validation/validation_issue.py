"""
Validation issue.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class ValidationIssue(BaseModel):
    """
    Represents one validation finding for a knowledge repository.
    """

    model_config = ConfigDict(frozen=True)

    severity: Literal["error", "warning"]

    code: str

    message: str

    domain: Optional[str] = None

    asset: Optional[str] = None