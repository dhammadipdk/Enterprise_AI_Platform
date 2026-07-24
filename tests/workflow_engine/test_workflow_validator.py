from enterprise_ai_platform.workflow_engine import (
    NodeType,
    RetryPolicy,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)
from enterprise_ai_platform.workflow_engine.validation.workflow_validator import (
    WorkflowValidator,
)


def _valid_definition() -> WorkflowDefinition:

    return WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
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


def test_valid_definition_has_no_issues() -> None:

    report = WorkflowValidator().validate(_valid_definition())

    assert report.is_valid

    assert report.warnings == []


def test_composes_compiler_structural_errors() -> None:
    # Same missing-End-node case the compiler itself catches -- the
    # validator's report must include it too, not just its own checks.

    definition = WorkflowDefinition(
        name="broken",
        version="1.0.0",
        entry_node="start",
        nodes=[WorkflowNode(id="start", name="Start", node_type=NodeType.START)],
        edges=[],
    )

    report = WorkflowValidator().validate(definition)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "MISSING_END_NODE" in codes


def test_retry_policy_zero_max_attempts_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="task",
                name="Task",
                node_type=NodeType.TASK,
                outputs=["result"],
                retry_policy=RetryPolicy(max_attempts=0),
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="task"),
            WorkflowEdge(source="task", destination="end"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "INVALID_RETRY_POLICY" in codes


def test_retry_policy_negative_backoff_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="task",
                name="Task",
                node_type=NodeType.TASK,
                outputs=["result"],
                retry_policy=RetryPolicy(backoff_seconds=-1.0),
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="task"),
            WorkflowEdge(source="task", destination="end"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "INVALID_RETRY_POLICY" in codes


def test_negative_timeout_is_an_error() -> None:

    definition = WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="task",
                name="Task",
                node_type=NodeType.TASK,
                outputs=["result"],
                timeout_seconds=-5.0,
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="task"),
            WorkflowEdge(source="task", destination="end"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    codes = {issue.code for issue in report.errors}

    assert "INVALID_TIMEOUT" in codes


def test_zero_timeout_is_a_warning_not_an_error() -> None:

    definition = WorkflowDefinition(
        name="explain_policy_question",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="task",
                name="Task",
                node_type=NodeType.TASK,
                outputs=["result"],
                timeout_seconds=0,
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="task"),
            WorkflowEdge(source="task", destination="end"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    assert report.is_valid

    codes = {issue.code for issue in report.warnings}

    assert "ZERO_TIMEOUT" in codes


def test_wait_node_without_duration_is_a_warning() -> None:

    definition = WorkflowDefinition(
        name="waity",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="pause", name="Pause", node_type=NodeType.WAIT),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="pause"),
            WorkflowEdge(source="pause", destination="end"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    assert report.is_valid

    codes = {issue.code for issue in report.warnings}

    assert "WAIT_NODE_NO_DURATION" in codes


def test_wait_node_with_duration_has_no_warning() -> None:

    definition = WorkflowDefinition(
        name="waity",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="pause",
                name="Pause",
                node_type=NodeType.WAIT,
                configuration={"duration_seconds": 5},
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="pause"),
            WorkflowEdge(source="pause", destination="end"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    assert report.warnings == []


def test_decision_node_without_outputs_is_a_warning() -> None:

    definition = WorkflowDefinition(
        name="decidey",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="decide", name="Decide", node_type=NodeType.DECISION),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="decide"),
            WorkflowEdge(source="decide", destination="end"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    codes = {issue.code for issue in report.warnings}

    assert "DECISION_NODE_NO_OUTPUTS" in codes


def test_duplicate_edge_is_a_warning() -> None:

    definition = WorkflowDefinition(
        name="dupey",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="end"),
            WorkflowEdge(source="start", destination="end"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    codes = {issue.code for issue in report.warnings}

    assert "DUPLICATE_EDGE" in codes


def test_different_conditions_are_not_duplicate_edges() -> None:

    definition = WorkflowDefinition(
        name="notdupey",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="decide",
                name="Decide",
                node_type=NodeType.DECISION,
                outputs=["flag_a", "flag_b"],
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            WorkflowEdge(source="start", destination="decide"),
            WorkflowEdge(source="decide", destination="end", condition="flag_a"),
            WorkflowEdge(source="decide", destination="end", condition="flag_b"),
        ],
    )

    report = WorkflowValidator().validate(definition)

    codes = {issue.code for issue in report.warnings}

    assert "DUPLICATE_EDGE" not in codes


def test_retry_policy_on_start_node_is_a_warning() -> None:

    definition = WorkflowDefinition(
        name="startretry",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(
                id="start",
                name="Start",
                node_type=NodeType.START,
                retry_policy=RetryPolicy(max_attempts=3),
            ),
            WorkflowNode(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[WorkflowEdge(source="start", destination="end")],
    )

    report = WorkflowValidator().validate(definition)

    assert report.is_valid

    codes = {issue.code for issue in report.warnings}

    assert "INEFFECTIVE_RETRY_POLICY" in codes


def test_timeout_on_end_node_is_a_warning() -> None:

    definition = WorkflowDefinition(
        name="endtimeout",
        version="1.0.0",
        entry_node="start",
        nodes=[
            WorkflowNode(id="start", name="Start", node_type=NodeType.START),
            WorkflowNode(
                id="end",
                name="End",
                node_type=NodeType.END,
                timeout_seconds=10.0,
            ),
        ],
        edges=[WorkflowEdge(source="start", destination="end")],
    )

    report = WorkflowValidator().validate(definition)

    codes = {issue.code for issue in report.warnings}

    assert "INEFFECTIVE_TIMEOUT" in codes