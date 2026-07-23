"""
Workflow edge.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WorkflowEdge(BaseModel):
    """
    Represents a transition between two workflow nodes.

    `condition` is an optional expression string evaluated at runtime
    (e.g. "output.status == 'approved'") -- the evaluation logic
    itself belongs to the Execution task, not here; this is purely the
    declarative edge shape.
    """

    model_config = ConfigDict(frozen=True)

    source: str

    destination: str

    condition: str | None = None

    priority: int = 0