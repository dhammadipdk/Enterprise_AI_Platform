"""
Execution definition.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.execution_engine.models.execution_retry_policy import (
    ExecutionRetryPolicy,
)


class ExecutionDefinition(BaseModel):
    """
    Describes how one kind of execution unit should be run (Section
    8): its timeout and retry behavior, priority, and free-form
    metadata.

    Deliberately has no "policy" field for queue-scheduling (unlike
    the spec's literal field list): scheduling (FIFO/priority/
    deadline) is a property of the QUEUE as a whole, decided once when
    constructing ExecutionEngineService, not something each individual
    unit definition should be able to override -- letting every unit
    pick its own scheduling algorithm would make queue ordering
    ill-defined the moment two different policies were mixed in one
    queue.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    description: str | None = None

    execution_type: str | None = None

    timeout_seconds: float | None = None

    retry_policy: ExecutionRetryPolicy = ExecutionRetryPolicy()

    priority: int = 0

    metadata: dict[str, Any] = {}