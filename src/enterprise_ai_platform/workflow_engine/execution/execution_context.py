"""
Execution context.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.workflow_engine.models import (
    NodeExecutionResult,
    WorkflowNode,
)


class ExecutionContext:
    """
    Mutable runtime state for one workflow execution (Section 14):
    variables, intermediate node results, and free-form metadata.

    Unlike every compiled artifact in this codebase (WorkflowGraph,
    PromptTemplate, etc.), this is deliberately mutable -- it's meant
    to accumulate state as execution proceeds through the graph, not
    to be a frozen snapshot.

    Keeps two separate views of node results, because they answer two
    different questions: `get_result(node_id)` answers "what was the
    latest result for this node" (a dict keyed by id -- a node visited
    twice, e.g. inside a Loop, overwrites its own entry), while
    `history()` answers "what was the full path execution actually
    took" (an append-only list -- the same node visited twice appears
    twice, in order). Conflating these was a real bug caught in
    testing: deriving history from the by-id dict silently collapsed
    repeated visits to the same node into a single entry.
    """

    def __init__(
        self,
        initial_variables: dict[str, Any] | None = None,
    ) -> None:

        self._variables: dict[str, Any] = dict(initial_variables or {})

        self._intermediate_results: dict[str, NodeExecutionResult] = {}

        self._history: list[NodeExecutionResult] = []

        self._metadata: dict[str, Any] = {}

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Return a variable's current value, or `default` if unset.
        """

        return self._variables.get(name, default)

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable's value.
        """

        self._variables[name] = value

    def variables(self) -> dict[str, Any]:
        """
        Return a copy of every current variable.
        """

        return dict(self._variables)

    def record_result(
        self,
        node: WorkflowNode,
        result: NodeExecutionResult,
    ) -> None:
        """
        Record a node's execution result.

        Updates both the by-id lookup (get_result) and the ordered,
        repeat-preserving history (history()). On success, any of the
        node's declared `outputs` present in the result's output dict
        are promoted into the shared variable namespace, so downstream
        nodes can read them by name -- this is the actual data-flow
        mechanism through the graph.
        """

        self._intermediate_results[node.id] = result

        self._history.append(result)

        if result.success:

            for output_name in node.outputs:

                if output_name in result.output:
                    self._variables[output_name] = result.output[
                        output_name
                    ]

    def get_result(self, node_id: str) -> NodeExecutionResult:
        """
        Return the most recent execution result recorded for a node.
        """

        if node_id not in self._intermediate_results:
            raise KeyError(
                f"No execution result recorded yet for node '{node_id}'."
            )

        return self._intermediate_results[node_id]

    def intermediate_results(self) -> dict[str, NodeExecutionResult]:
        """
        Return the most recent result for every node visited so far,
        keyed by node id. A node visited more than once (e.g. inside a
        Loop) only shows its latest result here -- use history() for
        the full ordered path including repeats.
        """

        return dict(self._intermediate_results)

    def history(self) -> list[NodeExecutionResult]:
        """
        Return every recorded result in the exact order execution
        visited them, including repeated visits to the same node.
        """

        return list(self._history)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata entry.
        """

        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Return a metadata entry, or `default` if unset.
        """

        return self._metadata.get(key, default)

    def metadata(self) -> dict[str, Any]:
        """
        Return a copy of all metadata.
        """

        return dict(self._metadata)