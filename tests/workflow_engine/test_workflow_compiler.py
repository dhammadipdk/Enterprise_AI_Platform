import pytest

from enterprise_ai_platform.workflow_engine import (
    NodeType,
    WorkflowCompiler,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)


def _valid_definition() -> WorkflowDefinition:
    """
    Mirrors the frozen spec's own Section 2 vision example:
    User Question -> Retrieve Knowledge -> Build Context ->
    Execute Prompt -> Validate Output -> Store Memory -> Return Response
    """

    nodes = [
        WorkflowNode(id="start", name="Start", node_type=NodeType.START),
        WorkflowNode(
            id="retrieve", name="Retrieve Knowledge", node_type=NodeType.KNOWLEDGE
        ),
        WorkflowNode(
            id="build_context", name="Build Context", node_type=NodeType.TASK
        ),
        WorkflowNode(
            id="execute_prompt", name="Execute Prompt", node_type=NodeType.LLM
        ),
        WorkflowNode(
            id="validate", name="Validate Output", node_type=NodeType.TASK
        ),
        WorkflowNode(
            id="store_memory", name="Store Memory", node_type=NodeType.MEMORY
        ),
        WorkflowNode(id="end", name="End", node_type=NodeType.END),
    ]

    edges = [
        WorkflowEdge(source="start", destination="retrieve"),
        WorkflowEdge(source="retrieve", destination="build_context"),
        WorkflowEdge(source="build_context", destination="execute_prompt"),
        WorkflowEdge(source="execute_prompt", destination="validate"),
        WorkflowEdge(source="validate", destination="store_memory"),
        WorkflowEdge(source="store_memory", destination="end"),
    ]

    return WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=nodes,
        edges=edges,
    )


def test_valid_definition_has_no_errors() -> None:

    report = WorkflowCompiler().validate(_valid_definition())

    assert report.is_valid


def test_compile_valid_definition_produces_graph() -> None:

    graph = WorkflowCompiler().compile(_valid_definition())

    assert graph.name == "explain_policy_question"

    assert graph.node_count() == 7

    assert graph.edge_count() == 6


def test_zero_start_nodes_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="a",
        nodes=[
            WorkflowNode(id="a", name="A", node_type=NodeType.TASK),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="a", destination="end")],
    )

    report = WorkflowCompiler().validate(definition)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "INVALID_START_NODE_COUNT" in codes


def test_two_start_nodes_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="start1",
        nodes=[
            WorkflowNode(id="start1", name="Start 1", node_type=NodeType.START),
            WorkflowNode(id="start2", name="Start 2", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start1", destination="end"),
            WorkflowEdge(source="start2", destination="end"),
        ],
    )

    report = WorkflowCompiler().validate(definition)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "INVALID_START_NODE_COUNT" in codes


def test_missing_end_node_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="a", name="A", node_type=NodeType.TASK),
        ],
        edges=[WorkflowEdge(source="start", destination="a")],
    )

    report = WorkflowCompiler().validate(definition)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "MISSING_END_NODE" in codes


def test_entry_node_not_referencing_a_real_node_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="does_not_exist",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="start", destination="end")],
    )

    report = WorkflowCompiler().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "INVALID_ENTRY_NODE" in codes


def test_entry_node_not_a_start_node_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="a",
        nodes=[
            WorkflowNode(id="a", name="A", node_type=NodeType.TASK),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="a", destination="end")],
    )

    report = WorkflowCompiler().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "ENTRY_NODE_NOT_START" in codes


def test_edge_referencing_unknown_node_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="start", destination="ghost_node")],
    )

    report = WorkflowCompiler().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "INVALID_EDGE_REFERENCE" in codes


def test_isolated_node_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
            WorkflowNode(
                id="orphan", name="Orphan", node_type=NodeType.TASK
            ),
        ],
        edges=[WorkflowEdge(source="start", destination="end")],
    )

    report = WorkflowCompiler().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "ISOLATED_NODE" in codes


def test_single_node_workflow_is_not_flagged_as_isolated() -> None:
    # Degenerate case: with only one node, "isolated" isn't meaningful.

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="only",
        nodes=[WorkflowNode(id="only", name="Only", node_type=NodeType.START)],
        edges=[],
    )

    report = WorkflowCompiler().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "ISOLATED_NODE" not in codes


def test_illegal_cycle_between_task_nodes_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="a", name="A", node_type=NodeType.TASK),
            WorkflowNode(id="b", name="B", node_type=NodeType.TASK),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="a"),
            WorkflowEdge(source="a", destination="b"),
            WorkflowEdge(source="b", destination="a"),
            WorkflowEdge(source="a", destination="end"),
        ],
    )

    report = WorkflowCompiler().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "ILLEGAL_CYCLE" in codes


def test_cycle_through_loop_node_is_allowed() -> None:

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

    report = WorkflowCompiler().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "ILLEGAL_CYCLE" not in codes

    assert report.is_valid


def test_compile_raises_on_invalid_definition() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="a",
        nodes=[WorkflowNode(id="a", name="A", node_type=NodeType.TASK)],
        edges=[],
    )

    with pytest.raises(ValueError, match="broken"):
        WorkflowCompiler().compile(definition)
        
def test_duplicate_node_ids_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="dup", name="First", node_type=NodeType.TASK),
            WorkflowNode(id="dup", name="Second", node_type=NodeType.TASK),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="dup"),
            WorkflowEdge(source="dup", destination="end"),
        ],
    )

    report = WorkflowCompiler().validate(definition)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "DUPLICATE_NODE_ID" in codes