import pytest

from enterprise_ai_platform.workflow_engine import (
    ExecutionState,
    NodeType,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowInstance,
    WorkflowNode,
)


def _graph():

    return WorkflowGraph(
        name="test_workflow",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="start", destination="end")],
    )


def test_initial_state_is_pending() -> None:

    instance = WorkflowInstance("i1", _graph())

    assert instance.state == ExecutionState.PENDING

    assert instance.current_node_id is None

    assert instance.started_at is None

    assert instance.completed_at is None

    assert instance.error is None

    assert not instance.is_terminal()


def test_node_history_empty_initially() -> None:

    instance = WorkflowInstance("i1", _graph())

    assert instance.node_history == []


def test_transition_to_terminal_marks_is_terminal() -> None:

    instance = WorkflowInstance("i1", _graph())

    instance._transition_to(ExecutionState.RUNNING)

    instance._transition_to(ExecutionState.COMPLETED)

    assert instance.is_terminal()


def test_cannot_transition_out_of_terminal_state() -> None:

    instance = WorkflowInstance("i1", _graph())

    instance._transition_to(ExecutionState.RUNNING)

    instance._transition_to(ExecutionState.FAILED)

    with pytest.raises(ValueError):
        instance._transition_to(ExecutionState.RUNNING)


def test_mark_started_and_completed_set_timestamps() -> None:

    instance = WorkflowInstance("i1", _graph())

    instance._mark_started()

    instance._mark_completed()

    assert instance.started_at is not None

    assert instance.completed_at is not None

    assert instance.completed_at >= instance.started_at


def test_set_error() -> None:

    instance = WorkflowInstance("i1", _graph())

    instance._set_error("something broke")

    assert instance.error == "something broke"


def test_default_context_is_created_automatically() -> None:

    instance = WorkflowInstance("i1", _graph())

    assert instance.context is not None

    assert instance.context.variables() == {}