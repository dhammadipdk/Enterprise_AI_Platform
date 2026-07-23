import pytest

from enterprise_ai_platform.workflow_engine import (
    NodeType,
    WorkflowDefinitionLoader,
)


def _valid_data():

    return {
        "name": "explain_policy_question",
        "version": "1.0.0",
        "entry_node": "start",
        "description": "Answers a customer's policy question.",
        "nodes": [
            {"id": "start", "name": "Start", "node_type": "start"},
            {
                "id": "retrieve",
                "name": "Retrieve context",
                "node_type": "knowledge",
                "configuration": {"repository": "insurance"},
                "inputs": ["question"],
                "outputs": ["context"],
                "retry_policy": {"max_attempts": 2, "backoff_seconds": 1.0},
                "timeout_seconds": 10.0,
            },
            {"id": "end", "name": "End", "node_type": "end"},
        ],
        "edges": [
            {"source": "start", "destination": "retrieve"},
            {"source": "retrieve", "destination": "end"},
        ],
        "metadata": {"owner": "explanation_agent"},
    }


def test_load_full_definition() -> None:

    loader = WorkflowDefinitionLoader()

    definition = loader.load(_valid_data())

    assert definition.name == "explain_policy_question"

    assert len(definition.nodes) == 3

    assert len(definition.edges) == 2

    assert definition.metadata["owner"] == "explanation_agent"


def test_node_types_resolved_correctly() -> None:

    loader = WorkflowDefinitionLoader()

    definition = loader.load(_valid_data())

    node_types = {node.id: node.node_type for node in definition.nodes}

    assert node_types["start"] == NodeType.START

    assert node_types["retrieve"] == NodeType.KNOWLEDGE

    assert node_types["end"] == NodeType.END


def test_retry_policy_parsed() -> None:

    loader = WorkflowDefinitionLoader()

    definition = loader.load(_valid_data())

    retrieve_node = next(n for n in definition.nodes if n.id == "retrieve")

    assert retrieve_node.retry_policy.max_attempts == 2

    assert retrieve_node.retry_policy.backoff_seconds == 1.0


def test_node_without_retry_policy_is_none() -> None:

    loader = WorkflowDefinitionLoader()

    definition = loader.load(_valid_data())

    start_node = next(n for n in definition.nodes if n.id == "start")

    assert start_node.retry_policy is None


def test_version_coerced_to_string() -> None:

    loader = WorkflowDefinitionLoader()

    data = _valid_data()

    data["version"] = 1.0

    definition = loader.load(data)

    assert definition.version == "1.0"


def test_missing_name_raises_clear_error() -> None:

    loader = WorkflowDefinitionLoader()

    data = _valid_data()

    del data["name"]

    with pytest.raises(ValueError, match="name"):
        loader.load(data)


def test_missing_entry_node_raises_clear_error() -> None:

    loader = WorkflowDefinitionLoader()

    data = _valid_data()

    del data["entry_node"]

    with pytest.raises(ValueError, match="entry_node"):
        loader.load(data)


def test_missing_node_id_raises_clear_error() -> None:

    loader = WorkflowDefinitionLoader()

    data = _valid_data()

    del data["nodes"][0]["id"]

    with pytest.raises(ValueError, match="id"):
        loader.load(data)