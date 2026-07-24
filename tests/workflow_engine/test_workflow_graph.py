import pytest

from enterprise_ai_platform.workflow_engine import (
    NodeType,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
)


def _graph():

    nodes = [
        WorkflowNode(id="start", name="Start", node_type=NodeType.START),
        WorkflowNode(id="retrieve", name="Retrieve", node_type=NodeType.KNOWLEDGE),
        WorkflowNode(id="end", name="End", node_type=NodeType.END),
    ]

    edges = [
        WorkflowEdge(source="start", destination="retrieve"),
        WorkflowEdge(source="retrieve", destination="end", priority=1),
        WorkflowEdge(source="retrieve", destination="start", priority=5),
    ]

    return WorkflowGraph(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=nodes,
        edges=edges,
        metadata={"owner": "explanation_agent"},
    )


def test_basic_properties() -> None:

    graph = _graph()

    assert graph.name == "explain_policy_question"

    assert graph.node_count() == 3

    assert graph.edge_count() == 3

    assert graph.metadata["owner"] == "explanation_agent"


def test_entry_node_returns_the_start_node() -> None:

    graph = _graph()

    assert graph.entry_node().id == "start"

    assert graph.entry_node().node_type == NodeType.START


def test_get_node_missing_raises_key_error() -> None:

    graph = _graph()

    with pytest.raises(KeyError):
        graph.get_node("does_not_exist")


def test_outgoing_edges_sorted_by_priority_descending() -> None:

    graph = _graph()

    edges = graph.outgoing_edges("retrieve")

    assert [edge.destination for edge in edges] == ["start", "end"]


def test_outgoing_edges_unsorted_preserves_original_order() -> None:

    graph = _graph()

    edges = graph.outgoing_edges("retrieve", sorted_by_priority=False)

    assert [edge.destination for edge in edges] == ["end", "start"]


def test_outgoing_edges_for_node_with_none_returns_empty() -> None:

    graph = _graph()

    assert graph.outgoing_edges("end") == []


def test_nodes_and_edges_return_copies() -> None:

    graph = _graph()

    nodes = graph.nodes

    nodes.append("not a real node")

    assert graph.node_count() == 3