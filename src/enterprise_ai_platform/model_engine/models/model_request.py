"""
Model request.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ModelRequest(BaseModel):
    """
    A single request to be sent to a model (Section 11).
    """

    model_config = ConfigDict(frozen=True)

    prompt: str

    request_id: str = Field(default_factory=lambda: str(uuid4()))

    system_prompt: str | None = None

    parameters: dict[str, Any] = {}

    context: dict[str, Any] | None = None

    attachments: list[Any] = []

    metadata: dict[str, Any] = {}