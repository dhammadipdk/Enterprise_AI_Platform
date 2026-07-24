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

    `response_schema` carries the JSON schema a caller wants the
    output to conform to, if any (Section 16). It's set here so the
    request is self-describing, but only the Model Engine's execute()
    currently *acts* on it (via StructuredOutputEnforcer); adapters
    are free to ignore it entirely, and none of them use it yet.
    A future task could let specific adapters use it for a provider-
    native structured-output mode without needing to touch this
    schema again.
    """

    model_config = ConfigDict(frozen=True)

    prompt: str

    request_id: str = Field(default_factory=lambda: str(uuid4()))

    system_prompt: str | None = None

    parameters: dict[str, Any] = {}

    context: dict[str, Any] | None = None

    attachments: list[Any] = []

    response_schema: dict[str, Any] | None = None

    metadata: dict[str, Any] = {}