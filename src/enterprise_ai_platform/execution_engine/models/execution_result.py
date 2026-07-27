"""
Execution result.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.execution_engine.models.execution_unit_state import (
    ExecutionUnitState,
)


class ExecutionResult(BaseModel):
    """
    The outcome of executing one ExecutionUnit (Section 7).
    """

    model_config = ConfigDict(frozen=True)

    request_id: str

    unit_name: str

    state: ExecutionUnitState

    result: Any = None

    error: str | None = None

    attempts: int = 0

    started_at: datetime | None = None

    completed_at: datetime | None = None

    duration_seconds: float | None = None