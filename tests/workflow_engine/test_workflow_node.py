import pytest

from enterprise_ai_platform.workflow_engine import (
    NodeType,
    RetryPolicy,
    WorkflowNode,
)


def test_defaults() -> None:

    node = WorkflowNode(id="n1", name="Start", node_type=NodeType.START)

    assert node.configuration == {}

    assert node.inputs == []

    assert node.outputs == []

    assert node.retry_policy is None

    assert node.timeout_seconds is None


def test_node_type_accepts_plain_string() -> None:

    node = WorkflowNode(id="n1", name="Do work", node_type="task")

    assert node.node_type == NodeType.TASK


def test_invalid_node_type_raises() -> None:

    with pytest.raises(Exception):
        WorkflowNode(id="n1", name="Bad", node_type="not_a_real_type")


def test_full_node() -> None:

    node = WorkflowNode(
        id="n2",
        name="Call model",
        node_type=NodeType.LLM,
        configuration={"prompt_name": "explain_zero_dep"},
        inputs=["question", "context"],
        outputs=["explanation"],
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=1.5),
        timeout_seconds=30.0,
        metadata={"owner": "explanation_agent"},
    )

    assert node.retry_policy.max_attempts == 3

    assert node.metadata["owner"] == "explanation_agent"


def test_is_frozen() -> None:

    node = WorkflowNode(id="n1", name="Start", node_type=NodeType.START)

    with pytest.raises(Exception):
        node.name = "changed"