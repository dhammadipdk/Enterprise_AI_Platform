"""
Workflow runtime.
"""

from __future__ import annotations

import time
from typing import Callable

from enterprise_ai_platform.workflow_engine.execution.execution_context import (
    ExecutionContext,
)
from enterprise_ai_platform.workflow_engine.execution.workflow_instance import (
    WorkflowInstance,
)
from enterprise_ai_platform.workflow_engine.graph import WorkflowGraph
from enterprise_ai_platform.workflow_engine.models import (
    ExecutionState,
    NodeExecutionResult,
    NodeType,
    WorkflowNode,
)

NodeHandler = Callable[[WorkflowNode, ExecutionContext], dict]


class WorkflowRuntime:
    """
    Executes a WorkflowInstance through its compiled graph, node by
    node.

    Node execution is dispatched to a pluggable handler registry
    (register_handler), the same extension pattern used throughout
    the Knowledge Engine (register_provider, register_chunking_
    strategy). Start/End are handled intrinsically; Wait gets a real
    default handler (time.sleep) since it needs nothing beyond the
    standard library. Every other node type (LLM, Tool, Knowledge,
    Decision, Task, Memory, Human Approval, Parallel, Loop, Custom)
    has no handler until one is explicitly registered, and executing
    an unhandled node type fails clearly rather than silently no-oping.

    Edge conditions are evaluated as context-variable truthiness
    checks, not arbitrary expressions -- see WorkflowEdge.condition's
    docstring for why. A Decision node's real job is producing the
    named boolean flags that downstream edges check.

    A max_steps guard protects against runaway execution. In practice
    this should be unreachable: WorkflowCompiler already rejects any
    cycle that doesn't pass through a Loop node, and Loop has no
    handler yet, so hitting one fails immediately rather than looping.
    The guard exists anyway as a hard backstop, not a relied-upon one.
    """

    DEFAULT_MAX_STEPS = 1000

    def __init__(self, max_steps: int = DEFAULT_MAX_STEPS) -> None:

        self._handlers: dict[NodeType, NodeHandler] = {}

        self._max_steps = max_steps

        self.register_handler(NodeType.WAIT, self._default_wait_handler)

    def register_handler(
        self,
        node_type: NodeType,
        handler: NodeHandler,
    ) -> None:
        """
        Register (or overwrite) the execution handler for a node type.
        """

        self._handlers[node_type] = handler

    def execute(self, instance: WorkflowInstance) -> WorkflowInstance:
        """
        Run `instance` to completion (or failure), mutating it in
        place, and return it.

        Raises ValueError if the instance isn't in PENDING state.
        """

        if instance.state != ExecutionState.PENDING:
            raise ValueError(
                f"Cannot execute instance '{instance.instance_id}': "
                f"already in state '{instance.state.value}'."
            )

        instance._transition_to(ExecutionState.RUNNING)

        instance._mark_started()

        current_node_id = instance.graph.entry_node_id

        steps = 0

        while True:

            steps += 1

            if steps > self._max_steps:
                return self._fail(
                    instance,
                    f"Exceeded maximum execution steps "
                    f"({self._max_steps}); likely infinite loop.",
                )


            node = instance.graph.get_node(current_node_id)

            instance._set_current_node(current_node_id)

            result = self._execute_node(node, instance.context)

            instance.context.record_result(node, result)

            if not result.success:
                return self._fail(instance, result.error or "Node failed.")

            if node.node_type == NodeType.END:
                instance._transition_to(ExecutionState.COMPLETED)
                instance._mark_completed()
                return instance


            next_node_id = self._select_next_node(
                instance.graph,
                node.id,
                instance.context,
            )

            if next_node_id is None:
                return self._fail(
                    instance,
                    f"No eligible outgoing edge from node '{node.id}'.",
                )

            current_node_id = next_node_id

    def cancel(self, instance: WorkflowInstance) -> WorkflowInstance:
        """
        Mark a non-terminal instance as cancelled.

        A no-op (returns the instance unchanged) if it has already
        reached a terminal state.
        """

        if not instance.is_terminal():
            instance._transition_to(ExecutionState.CANCELLED)
            instance._mark_completed()

        return instance

    def _execute_node(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
    ) -> NodeExecutionResult:

        if node.node_type in (NodeType.START, NodeType.END):
            return NodeExecutionResult(node_id=node.id, success=True)

        handler = self._handlers.get(node.node_type)

        if handler is None:
            return NodeExecutionResult(
                node_id=node.id,
                success=False,
                error=(
                    f"No execution handler registered for node type "
                    f"'{node.node_type.value}' (node '{node.id}')."
                ),
            )

        try:
            output = handler(node, context)
            return NodeExecutionResult(
                node_id=node.id,
                success=True,
                output=output or {},
            )
        except Exception as error:
            return NodeExecutionResult(
                node_id=node.id,
                success=False,
                error=str(error),
            )

    @staticmethod
    def _select_next_node(
        graph: WorkflowGraph,
        node_id: str,
        context: ExecutionContext,
    ) -> str | None:

        for edge in graph.outgoing_edges(node_id):

            if edge.condition is None:
                return edge.destination

            if bool(context.get_variable(edge.condition)):
                return edge.destination

        return None

    @staticmethod
    def _fail(instance: WorkflowInstance, message: str) -> WorkflowInstance:

        instance._transition_to(ExecutionState.FAILED)

        instance._set_error(message)

        instance._mark_completed()

        return instance

    @staticmethod
    def _default_wait_handler(
        node: WorkflowNode,
        context: ExecutionContext,
    ) -> dict:

        duration = node.configuration.get("duration_seconds", 0)

        if duration:
            time.sleep(duration)

        return {}