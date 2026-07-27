"""
Execution unit state.
"""

from __future__ import annotations

from enum import Enum


class ExecutionUnitState(str, Enum):
    """
    Lifecycle state of one ExecutionUnit's execution (Section 12).

    Named ExecutionUnitState, not ExecutionState, to avoid colliding
    with workflow_engine.models.ExecutionState -- a different enum
    with a different value set describing a WorkflowInstance's state,
    not a single generic execution unit's.

    Simplified from the spec's Queued -> Scheduled -> Running ->
    ... to drop the Queued/Scheduled distinction: for this task's
    single-threaded, synchronous design there's no meaningful
    difference between "queued" and "scheduled" until something is
    actually RUNNING, so they collapse into QUEUED.
    """

    QUEUED = "queued"

    RUNNING = "running"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"

    TIMED_OUT = "timed_out"