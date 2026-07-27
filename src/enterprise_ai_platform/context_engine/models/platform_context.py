"""
Platform context.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class PlatformContext(BaseModel):
    """
    The fully assembled, immutable execution context (Section 8 of
    the frozen spec, which names this "ExecutionContext").

    Renamed to PlatformContext here to avoid colliding with
    workflow_engine.execution.ExecutionContext, which is a completely
    different thing -- mutable, workflow-specific variable state built
    up node-by-node during one execution. This object is the opposite
    in every relevant way: immutable, assembled once from many
    sources (Knowledge, Memory, Workflow, User, Tool, Model), and
    handed to Prompt Engine / Model Engine as input. Since both are
    genuinely going to be imported together once the platform is
    wired end-to-end, giving them the same name would have been a
    real source of confusion later, not just now.
    """

    model_config = ConfigDict(frozen=True)

    context_id: str = Field(default_factory=lambda: str(uuid4()))

    workflow_context: dict[str, Any] = {}

    knowledge_context: dict[str, Any] = {}

    memory_context: dict[str, Any] = {}

    user_context: dict[str, Any] = {}

    execution_context: dict[str, Any] = {}

    tool_context: dict[str, Any] = {}

    model_context: dict[str, Any] = {}

    metadata: dict[str, Any] = {}