import pytest

from enterprise_ai_platform.workflow_engine import (
    NodeType,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)


def _nodes():

    return [
        WorkflowNode(id="start", name="Start", node_type=NodeType.START),
        WorkflowNode(id="end", name="End", node_type=NodeType.END),
    ]


def test_minimal_definition() -> None:

    definition = WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=_nodes(),
    )

    assert definition.edges == []

    assert definition.description is None

    assert definition.metadata == {}


def test_full_definition() -> None:

    definition = WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=_nodes(),
        edges=[WorkflowEdge(source="start", destination="end")],
        description="Answers a customer's policy question.",
        metadata={"owner": "explanation_agent"},
    )

    assert len(definition.edges) == 1

    assert definition.metadata["owner"] == "explanation_agent"


def test_is_frozen() -> None:

    definition = WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=_nodes(),
    )

    with pytest.raises(Exception):
        definition.version = "2.0.0"