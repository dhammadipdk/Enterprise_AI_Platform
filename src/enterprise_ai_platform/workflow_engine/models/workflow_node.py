"""
Workflow node.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.workflow_engine.models.node_type import NodeType
from enterprise_ai_platform.workflow_engine.models.retry_policy import (
    RetryPolicy,
)


class WorkflowNode(BaseModel):
    """
    Represents one execution step in a workflow.
    """

    model_config = ConfigDict(frozen=True)

    id: str

    name: str

    node_type: NodeType

    configuration: dict[str, Any] = {}

    inputs: list[str] = []

    outputs: list[str] = []

    retry_policy: RetryPolicy | None = None

    timeout_seconds: float | None = None

    metadata: dict[str, Any] = {}