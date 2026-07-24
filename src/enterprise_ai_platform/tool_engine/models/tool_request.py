"""
Tool request.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ToolRequest(BaseModel):
    """
    A single request to execute a tool (Section 10).
    """

    model_config = ConfigDict(frozen=True)

    tool_name: str

    parameters: dict[str, Any] = {}

    request_id: str = Field(default_factory=lambda: str(uuid4()))

    execution_context: dict[str, Any] | None = None

    timeout_seconds: float | None = None

    priority: int = 0

    metadata: dict[str, Any] = {}