"""
Workflow instance.
"""

from __future__ import annotations

from datetime import datetime, timezone

from enterprise_ai_platform.workflow_engine.execution.execution_context import (
    ExecutionContext,
)
from enterprise_ai_platform.workflow_engine.graph import WorkflowGraph
from enterprise_ai_platform.workflow_engine.models import (
    ExecutionState,
    NodeExecutionResult,
)

_TERMINAL_STATES = (
    ExecutionState.COMPLETED,
    ExecutionState.FAILED,
    ExecutionState.CANCELLED,
)


class WorkflowInstance:
    """
    Represents one running (or completed) execution of a compiled
    WorkflowGraph (Section 13).

    Deliberately mutable, unlike PromptInstance in the Prompt Engine
    -- a PromptInstance is an immutable snapshot of one already-
    completed render, whereas a WorkflowInstance's whole purpose is to
    track state (current_node, execution_state, node history) that
    genuinely changes over the course of a multi-step execution.

    The `_`-prefixed mutator methods are meant to be called only by
    WorkflowRuntime as it drives execution forward, not by external
    callers -- the same "protected but not enforced" convention as
    BaseComponent._set_state elsewhere in this codebase.
    """

    def __init__(
        self,
        instance_id: str,
        graph: WorkflowGraph,
        context: ExecutionContext | None = None,
    ) -> None:

        self._instance_id = instance_id

        self._graph = graph

        self._current_node_id: str | None = None

        self._state = ExecutionState.PENDING

        self._context = context if context is not None else ExecutionContext()

        self._created_at = datetime.now(timezone.utc)

        self._started_at: datetime | None = None

        self._completed_at: datetime | None = None

        self._error: str | None = None

    @property
    def instance_id(self) -> str:
        """
        Return this instance's unique id.
        """

        return self._instance_id

    @property
    def graph(self) -> WorkflowGraph:
        """
        Return the compiled graph this instance is executing.
        """

        return self._graph

    @property
    def current_node_id(self) -> str | None:
        """
        Return the id of the node currently (or most recently) being
        executed, or None if execution hasn't started.
        """

        return self._current_node_id

    @property
    def state(self) -> ExecutionState:
        """
        Return the current execution state.
        """

        return self._state

    @property
    def context(self) -> ExecutionContext:
        """
        Return this instance's execution context.
        """

        return self._context

    @property
    def created_at(self) -> datetime:
        """
        Return when this instance was created.
        """

        return self._created_at

    @property
    def started_at(self) -> datetime | None:
        """
        Return when execution started, or None if not yet started.
        """

        return self._started_at

    @property
    def completed_at(self) -> datetime | None:
        """
        Return when execution reached a terminal state, or None if
        still running.
        """

        return self._completed_at

    @property
    def error(self) -> str | None:
        """
        Return the error message if execution failed, else None.
        """

        return self._error

    @property
    def node_history(self) -> list[NodeExecutionResult]:
        """
        Return every node's execution result in the exact order they
        were visited, including the End node and including repeated
        visits to the same node (e.g. inside a Loop).
        """

        return self._context.history()

    def is_terminal(self) -> bool:
        """
        Return True if execution has reached a final state (completed,
        failed, or cancelled).
        """

        return self._state in _TERMINAL_STATES

    def _set_current_node(self, node_id: str) -> None:

        self._current_node_id = node_id

    def _transition_to(self, state: ExecutionState) -> None:

        if self.is_terminal():
            raise ValueError(
                f"Cannot transition instance '{self._instance_id}' to "
                f"'{state.value}': already in terminal state "
                f"'{self._state.value}'."
            )

        self._state = state

    def _mark_started(self) -> None:

        self._started_at = datetime.now(timezone.utc)

    def _mark_completed(self) -> None:

        self._completed_at = datetime.now(timezone.utc)

    def _set_error(self, message: str) -> None:

        self._error = message