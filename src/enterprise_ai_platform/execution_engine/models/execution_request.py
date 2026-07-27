"""
Execution request.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ExecutionRequest(BaseModel):
    """
    A single request to submit one ExecutionUnit for execution
    (Section 9).
    """

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(default_factory=lambda: str(uuid4()))

    workflow_id: str | None = None

    task_id: str | None = None

    context: dict[str, Any] = {}

    priority: int = 0

    deadline: datetime | None = None

    metadata: dict[str, Any] = {}