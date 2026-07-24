"""
Tool response.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ToolResponse(BaseModel):
    """
    A tool's response to one ToolRequest (Section 11).

    `execution_time_seconds` is always set by ToolService itself
    (measured uniformly around the adapter call), not by individual
    adapters -- so timing is consistent regardless of whether a given
    adapter remembers to measure it.
    """

    model_config = ConfigDict(frozen=True)

    request_id: str

    status: Literal["success", "failure"]

    response_id: str = Field(default_factory=lambda: str(uuid4()))

    result: Any = None

    error: str | None = None

    artifacts: list[Any] = []

    execution_time_seconds: float | None = None

    metadata: dict[str, Any] = {}