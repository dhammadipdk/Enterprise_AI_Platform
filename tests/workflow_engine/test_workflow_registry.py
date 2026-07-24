import pytest

from enterprise_ai_platform.workflow_engine import (
    NodeType,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
    WorkflowRegistry,
)


def _graph(name="explain_policy_question", version="1.0.0"):

    return WorkflowGraph(
        name=name,
        version=version,
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="start", destination="end")],
    )


def test_register_and_get() -> None:

    registry = WorkflowRegistry()

    registry.register("explain_policy_question@1.0.0", _graph())

    retrieved = registry.get("explain_policy_question@1.0.0")

    assert retrieved.name == "explain_policy_question"


def test_exists() -> None:

    registry = WorkflowRegistry()

    assert not registry.exists("explain_policy_question@1.0.0")

    registry.register("explain_policy_question@1.0.0", _graph())

    assert registry.exists("explain_policy_question@1.0.0")


def test_get_missing_raises_key_error() -> None:

    registry = WorkflowRegistry()

    with pytest.raises(KeyError):
        registry.get("does_not_exist@1.0.0")


def test_clear_removes_everything() -> None:

    registry = WorkflowRegistry()

    registry.register("explain_policy_question@1.0.0", _graph())

    registry.clear()

    assert registry.names() == []