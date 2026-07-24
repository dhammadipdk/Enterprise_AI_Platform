import pytest

from enterprise_ai_platform.workflow_engine import (
    ExecutionContext,
    NodeExecutionResult,
    NodeType,
    WorkflowNode,
)


def test_default_variables_empty() -> None:

    context = ExecutionContext()

    assert context.variables() == {}


def test_initial_variables() -> None:

    context = ExecutionContext(initial_variables={"question": "hi"})

    assert context.get_variable("question") == "hi"


def test_get_variable_default() -> None:

    context = ExecutionContext()

    assert context.get_variable("missing", default="fallback") == "fallback"


def test_set_variable() -> None:

    context = ExecutionContext()

    context.set_variable("tone", "formal")

    assert context.get_variable("tone") == "formal"


def test_record_result_promotes_declared_outputs() -> None:

    context = ExecutionContext()

    node = WorkflowNode(
        id="retrieve",
        name="Retrieve",
        node_type=NodeType.KNOWLEDGE,
        outputs=["context_text"],
    )

    result = NodeExecutionResult(
        node_id="retrieve",
        success=True,
        output={"context_text": "policy clause text", "extra": "ignored"},
    )

    context.record_result(node, result)

    assert context.get_variable("context_text") == "policy clause text"

    assert context.get_variable("extra") is None


def test_record_result_does_not_promote_output_on_failure() -> None:

    context = ExecutionContext()

    node = WorkflowNode(
        id="retrieve",
        name="Retrieve",
        node_type=NodeType.KNOWLEDGE,
        outputs=["context_text"],
    )

    result = NodeExecutionResult(
        node_id="retrieve",
        success=False,
        output={"context_text": "should not be promoted"},
        error="boom",
    )

    context.record_result(node, result)

    assert context.get_variable("context_text") is None


def test_get_result_returns_recorded_result() -> None:

    context = ExecutionContext()

    node = WorkflowNode(id="n1", name="N1", node_type=NodeType.TASK)

    result = NodeExecutionResult(node_id="n1", success=True)

    context.record_result(node, result)

    assert context.get_result("n1") is result


def test_get_result_missing_raises_key_error() -> None:

    context = ExecutionContext()

    with pytest.raises(KeyError):
        context.get_result("does_not_exist")


def test_intermediate_results_preserves_execution_order() -> None:

    context = ExecutionContext()

    for node_id in ["a", "b", "c"]:
        node = WorkflowNode(id=node_id, name=node_id, node_type=NodeType.TASK)
        context.record_result(
            node, NodeExecutionResult(node_id=node_id, success=True)
        )

    assert list(context.intermediate_results().keys()) == ["a", "b", "c"]


def test_metadata() -> None:

    context = ExecutionContext()

    context.set_metadata("triggered_by", "api")

    assert context.get_metadata("triggered_by") == "api"

    assert context.get_metadata("missing") is None
    
def test_history_preserves_repeated_visits_to_the_same_node() -> None:
    """
    Regression test: intermediate_results() is a by-id dict and
    correctly overwrites on repeat visits (it answers "what's the
    latest result for this node"), but history() must NOT collapse
    repeats -- it answers "what path did execution actually take",
    which needs every visit, including revisits inside a Loop.
    """

    context = ExecutionContext()

    loop_node = WorkflowNode(id="loop_node", name="Loop", node_type=NodeType.LOOP)

    for _ in range(3):
        context.record_result(
            loop_node,
            NodeExecutionResult(node_id="loop_node", success=True),
        )

    assert len(context.intermediate_results()) == 1

    assert len(context.history()) == 3

    assert [result.node_id for result in context.history()] == [
        "loop_node",
        "loop_node",
        "loop_node",
    ]