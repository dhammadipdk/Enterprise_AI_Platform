"""
Model response.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ModelResponse(BaseModel):
    """
    A model's response to one ModelRequest (Section 12).
    """

    model_config = ConfigDict(frozen=True)

    request_id: str

    text: str

    response_id: str = Field(default_factory=lambda: str(uuid4()))

    structured_output: dict[str, Any] | None = None

    tool_calls: list[Any] = []

    token_usage: dict[str, int] = {}

    cost: float | None = None

    latency_seconds: float | None = None

    metadata: dict[str, Any] = {}