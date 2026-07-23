"""
Workflow definition.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.workflow_engine.models.workflow_edge import (
    WorkflowEdge,
)
from enterprise_ai_platform.workflow_engine.models.workflow_node import (
    WorkflowNode,
)


class WorkflowDefinition(BaseModel):
    """
    An immutable workflow definition -- the raw, as-authored graph
    description, before compilation into a WorkflowGraph (a later
    Workflow Engine step).
    """

    model_config = ConfigDict(frozen=True)

    name: str

    version: str

    entry_node: str

    nodes: list[WorkflowNode]

    edges: list[WorkflowEdge] = []

    description: str | None = None

    metadata: dict[str, Any] = {}