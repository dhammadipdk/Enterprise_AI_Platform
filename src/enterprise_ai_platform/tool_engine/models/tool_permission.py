"""
Tool permission.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ToolPermission(BaseModel):
    """
    One named permission a tool may require before it can be executed
    (Section 14: Application / Agent / Workflow / User / Organization
    Permission -- this models any one of those scopes generically).
    """

    model_config = ConfigDict(frozen=True)

    name: str

    description: str | None = None