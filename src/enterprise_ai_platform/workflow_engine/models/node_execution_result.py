"""
Node execution result.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class NodeExecutionResult(BaseModel):
    """
    The outcome of executing a single workflow node.
    """

    model_config = ConfigDict(frozen=True)

    node_id: str

    success: bool

    output: dict[str, Any] = {}

    error: str | None = None