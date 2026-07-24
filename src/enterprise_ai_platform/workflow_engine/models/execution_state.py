"""
Execution state.
"""

from __future__ import annotations

from enum import Enum


class ExecutionState(str, Enum):
    """
    Lifecycle state of one running WorkflowInstance.

    Distinct from the frozen spec's Section 15 definition-level stages
    (Registered / Validated / Compiled / Ready) -- those describe
    whether a WorkflowDefinition is safe to execute at all (already
    handled synchronously by WorkflowCompiler), while this describes
    an actual in-progress execution's state over time.
    """

    PENDING = "pending"

    RUNNING = "running"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"