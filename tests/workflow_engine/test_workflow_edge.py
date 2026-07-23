import pytest

from enterprise_ai_platform.workflow_engine import WorkflowEdge


def test_defaults() -> None:

    edge = WorkflowEdge(source="n1", destination="n2")

    assert edge.condition is None

    assert edge.priority == 0


def test_conditional_edge() -> None:

    edge = WorkflowEdge(
        source="decision",
        destination="approved_path",
        condition="output.status == 'approved'",
        priority=1,
    )

    assert edge.condition == "output.status == 'approved'"


def test_is_frozen() -> None:

    edge = WorkflowEdge(source="n1", destination="n2")

    with pytest.raises(Exception):
        edge.priority = 5