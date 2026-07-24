import pytest

from enterprise_ai_platform.workflow_engine import (
    ExecutionState,
    NodeType,
    WorkflowCompiler,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowInstance,
    WorkflowNode,
    WorkflowRuntime,
)


def _compile(nodes, edges, entry_node="start"):

    definition = WorkflowDefinition(
        name="test_workflow",
        version="1.0.0",
        entry_node=entry_node,
        nodes=nodes,
        edges=edges,
    )

    return WorkflowCompiler().compile(definition)


def test_simple_linear_workflow_completes() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="task", name="Task", node_type=NodeType.TASK, outputs=["result"]
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="task"),
            WorkflowEdge(source="task", destination="end"),
        ],
    )

    runtime = WorkflowRuntime()

    runtime.register_handler(
        NodeType.TASK, lambda node, ctx: {"result": "hello"}
    )

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert instance.state == ExecutionState.COMPLETED

    assert instance.context.get_variable("result") == "hello"

    assert [r.node_id for r in instance.node_history] == [
        "start",
        "task",
        "end",
    ]


def test_conditional_branch_takes_approved_path() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="decide",
                name="Decide",
                node_type=NodeType.DECISION,
                outputs=["approved"],
            ),
            WorkflowNode(
                id="approved_path", name="Approved", node_type=NodeType.TASK
            ),
            WorkflowNode(
                id="rejected_path", name="Rejected", node_type=NodeType.TASK
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="decide"),
            WorkflowEdge(
                source="decide",
                destination="approved_path",
                condition="approved",
                priority=1,
            ),
            WorkflowEdge(
                source="decide", destination="rejected_path", priority=0
            ),
            WorkflowEdge(source="approved_path", destination="end"),
            WorkflowEdge(source="rejected_path", destination="end"),
        ],
    )

    runtime = WorkflowRuntime()

    runtime.register_handler(
        NodeType.DECISION, lambda node, ctx: {"approved": True}
    )

    runtime.register_handler(NodeType.TASK, lambda node, ctx: {})

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert instance.state == ExecutionState.COMPLETED

    assert [r.node_id for r in instance.node_history] == [
        "start",
        "decide",
        "approved_path",
        "end",
    ]


def test_conditional_branch_falls_back_to_unconditional_edge() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="decide",
                name="Decide",
                node_type=NodeType.DECISION,
                outputs=["approved"],
            ),
            WorkflowNode(
                id="approved_path", name="Approved", node_type=NodeType.TASK
            ),
            WorkflowNode(
                id="rejected_path", name="Rejected", node_type=NodeType.TASK
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="decide"),
            WorkflowEdge(
                source="decide",
                destination="approved_path",
                condition="approved",
                priority=1,
            ),
            WorkflowEdge(
                source="decide", destination="rejected_path", priority=0
            ),
            WorkflowEdge(source="approved_path", destination="end"),
            WorkflowEdge(source="rejected_path", destination="end"),
        ],
    )

    runtime = WorkflowRuntime()

    runtime.register_handler(
        NodeType.DECISION, lambda node, ctx: {"approved": False}
    )

    runtime.register_handler(NodeType.TASK, lambda node, ctx: {})

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert [r.node_id for r in instance.node_history] == [
        "start",
        "decide",
        "rejected_path",
        "end",
    ]


def test_unregistered_node_type_fails_cleanly() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="call_llm", name="Call LLM", node_type=NodeType.LLM),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="call_llm"),
            WorkflowEdge(source="call_llm", destination="end"),
        ],
    )

    runtime = WorkflowRuntime()

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert instance.state == ExecutionState.FAILED

    assert "no execution handler" in instance.error.lower()


def test_handler_reporting_failure_fails_the_instance() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="risky", name="Risky", node_type=NodeType.TASK),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="risky"),
            WorkflowEdge(source="risky", destination="end"),
        ],
    )

    runtime = WorkflowRuntime()

    def _raise(node, ctx):
        raise RuntimeError("simulated tool failure")

    runtime.register_handler(NodeType.TASK, _raise)

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert instance.state == ExecutionState.FAILED

    assert "simulated tool failure" in instance.error


def test_dead_end_with_no_eligible_edge_fails() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="decide",
                name="Decide",
                node_type=NodeType.DECISION,
                outputs=["go"],
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="decide"),
            WorkflowEdge(source="decide", destination="end", condition="go"),
        ],
    )

    runtime = WorkflowRuntime()

    runtime.register_handler(
        NodeType.DECISION, lambda node, ctx: {"go": False}
    )

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert instance.state == ExecutionState.FAILED

    assert "no eligible outgoing edge" in instance.error.lower()


def test_wait_node_has_a_working_default_handler() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="pause",
                name="Pause",
                node_type=NodeType.WAIT,
                configuration={"duration_seconds": 0},
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="pause"),
            WorkflowEdge(source="pause", destination="end"),
        ],
    )

    runtime = WorkflowRuntime()

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert instance.state == ExecutionState.COMPLETED


def test_max_steps_guard_trips_on_runaway_loop() -> None:

    definition = WorkflowDefinition(
        name="loopy",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="loop_node", name="Loop", node_type=NodeType.LOOP
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="loop_node"),
            WorkflowEdge(source="loop_node", destination="loop_node"),
            WorkflowEdge(source="loop_node", destination="end"),
        ],
    )

    graph = WorkflowCompiler().compile(definition)

    runtime = WorkflowRuntime(max_steps=5)

    runtime.register_handler(NodeType.LOOP, lambda node, ctx: {})

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert instance.state == ExecutionState.FAILED

    assert "maximum execution steps" in instance.error.lower()

    assert len(instance.node_history) == 5


def test_execute_raises_if_instance_already_run() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="start", destination="end")],
    )

    runtime = WorkflowRuntime()

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    with pytest.raises(ValueError):
        runtime.execute(instance)


def test_cancel_marks_running_instance_cancelled() -> None:

    instance = WorkflowInstance(
        "i1",
        _compile(
            nodes=[
                WorkflowNode(id="start", name="Start", node_type=NodeType.START),
                WorkflowNode(id="end", name="End", node_type=NodeType.END),
            ],
            edges=[WorkflowEdge(source="start", destination="end")],
        ),
    )

    instance._transition_to(ExecutionState.RUNNING)

    runtime = WorkflowRuntime()

    runtime.cancel(instance)

    assert instance.state == ExecutionState.CANCELLED

    assert instance.is_terminal()


def test_cancel_is_a_no_op_on_already_terminal_instance() -> None:

    graph = _compile(
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="start", destination="end")],
    )

    runtime = WorkflowRuntime()

    instance = WorkflowInstance("i1", graph)

    runtime.execute(instance)

    assert instance.state == ExecutionState.COMPLETED

    runtime.cancel(instance)

    assert instance.state == ExecutionState.COMPLETED