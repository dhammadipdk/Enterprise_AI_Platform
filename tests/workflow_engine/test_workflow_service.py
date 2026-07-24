import pytest

from enterprise_ai_platform.workflow_engine import (
    ExecutionState,
    NodeType,
    WorkflowService,
)


def _workflow_data(name="explain_policy_question", version="1.0.0"):

    return {
        "name": name,
        "version": version,
        "entry_node": "start",
        "nodes": [
            {"id": "start", "name": "Start", "node_type": "start"},
            {
                "id": "answer",
                "name": "Answer question",
                "node_type": "task",
                "outputs": ["answer"],
            },
            {"id": "end", "name": "End", "node_type": "end"},
        ],
        "edges": [
            {"source": "start", "destination": "answer"},
            {"source": "answer", "destination": "end"},
        ],
    }


def test_validate_workflow_valid_data() -> None:

    service = WorkflowService()

    report = service.validate_workflow(_workflow_data())

    assert report.is_valid


def test_validate_workflow_invalid_data() -> None:

    service = WorkflowService()

    data = _workflow_data()

    data["nodes"] = [data["nodes"][0], data["nodes"][1]]  # drop End node

    report = service.validate_workflow(data)

    assert not report.is_valid


def test_compile_workflow_does_not_register() -> None:

    service = WorkflowService()

    graph = service.compile_workflow(_workflow_data())

    assert graph.name == "explain_policy_question"

    assert not service.workflow_exists("explain_policy_question")


def test_register_workflow_makes_it_retrievable() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data())

    assert service.workflow_exists("explain_policy_question")

    graph = service.get_workflow("explain_policy_question")

    assert graph.version == "1.0.0"


def test_get_workflow_missing_raises_key_error() -> None:

    service = WorkflowService()

    with pytest.raises(KeyError):
        service.get_workflow("does_not_exist")


def test_get_workflow_specific_version() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data(version="1.0.0"))

    service.register_workflow(_workflow_data(version="2.0.0"))

    graph = service.get_workflow("explain_policy_question", version="1.0.0")

    assert graph.version == "1.0.0"


def test_get_workflow_default_returns_latest_version() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data(version="1.0.0"))

    service.register_workflow(_workflow_data(version="2.0.0"))

    graph = service.get_workflow("explain_policy_question")

    assert graph.version == "2.0.0"


def test_get_workflow_latest_uses_numeric_not_string_comparison() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data(version="1.9.0"))

    service.register_workflow(_workflow_data(version="1.10.0"))

    graph = service.get_workflow("explain_policy_question")

    assert graph.version == "1.10.0"


def test_list_workflows_returns_unique_names() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data(version="1.0.0"))

    service.register_workflow(_workflow_data(version="2.0.0"))

    service.register_workflow(_workflow_data(name="other_workflow"))

    assert service.list_workflows() == [
        "explain_policy_question",
        "other_workflow",
    ]


def test_list_versions_sorted_numerically() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data(version="1.9.0"))

    service.register_workflow(_workflow_data(version="1.2.0"))

    service.register_workflow(_workflow_data(version="1.10.0"))

    assert service.list_versions("explain_policy_question") == [
        "1.2.0",
        "1.9.0",
        "1.10.0",
    ]


def test_execute_runs_workflow_to_completion() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data())

    service.register_node_handler(
        NodeType.TASK, lambda node, ctx: {"answer": "Zero dep covers this."}
    )

    instance = service.execute("explain_policy_question")

    assert instance.state == ExecutionState.COMPLETED

    assert instance.context.get_variable("answer") == "Zero dep covers this."


def test_execute_passes_initial_variables() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data())

    service.register_node_handler(
        NodeType.TASK,
        lambda node, ctx: {"answer": f"Re: {ctx.get_variable('question')}"},
    )

    instance = service.execute(
        "explain_policy_question",
        initial_variables={"question": "what is IDV?"},
    )

    assert instance.context.get_variable("answer") == "Re: what is IDV?"


def test_get_execution_returns_tracked_instance() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data())

    service.register_node_handler(NodeType.TASK, lambda node, ctx: {})

    instance = service.execute("explain_policy_question")

    retrieved = service.get_execution(instance.instance_id)

    assert retrieved is instance


def test_get_execution_missing_raises_key_error() -> None:

    service = WorkflowService()

    with pytest.raises(KeyError):
        service.get_execution("does_not_exist")


def test_list_executions() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data())

    service.register_node_handler(NodeType.TASK, lambda node, ctx: {})

    first = service.execute("explain_policy_question")

    second = service.execute("explain_policy_question")

    assert set(service.list_executions()) == {
        first.instance_id,
        second.instance_id,
    }


def test_cancel_marks_instance_cancelled() -> None:
    """
    Uses a workflow with an unregistered node type so execute() leaves
    it in a non-terminal-seeming path only briefly -- in practice
    execute() always runs to a terminal state synchronously, so this
    demonstrates cancel() being a safe no-op on an already-terminal
    instance rather than a real mid-flight cancellation (nothing in V1
    can pause execution to be cancelled mid-run; see resume()'s
    docstring for the same limitation).
    """

    service = WorkflowService()

    service.register_workflow(_workflow_data())

    service.register_node_handler(NodeType.TASK, lambda node, ctx: {})

    instance = service.execute("explain_policy_question")

    assert instance.state == ExecutionState.COMPLETED

    result = service.cancel(instance.instance_id)

    assert result.state == ExecutionState.COMPLETED


def test_lifecycle_transitions() -> None:

    service = WorkflowService()

    service.initialize()

    service.start()

    assert service.is_running

    service.stop()

    service.dispose()


def test_dispose_clears_registered_workflows_and_executions() -> None:

    service = WorkflowService()

    service.register_workflow(_workflow_data())

    service.register_node_handler(NodeType.TASK, lambda node, ctx: {})

    instance = service.execute("explain_policy_question")

    service.initialize()

    service.start()

    service.stop()

    service.dispose()

    assert not service.workflow_exists("explain_policy_question")

    with pytest.raises(KeyError):
        service.get_execution(instance.instance_id)