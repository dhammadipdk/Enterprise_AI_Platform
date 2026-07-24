import pytest

from enterprise_ai_platform.tool_engine import (
    ToolCategory,
    ToolDefinition,
    ToolPermission,
)


def test_defaults() -> None:

    tool = ToolDefinition(name="check_policy_status", version="1.0.0")

    assert tool.category == ToolCategory.CUSTOM

    assert tool.input_schema is None

    assert tool.output_schema is None

    assert tool.permissions == []

    assert tool.owner is None


def test_full_definition() -> None:

    tool = ToolDefinition(
        name="check_policy_status",
        version="1.0.0",
        description="Looks up a customer's current policy status.",
        category=ToolCategory.DATABASE,
        input_schema={"type": "object", "properties": {"policy_id": {"type": "string"}}},
        permissions=[ToolPermission(name="read_customer_data")],
        owner="insureai-platform-team",
    )

    assert tool.category == ToolCategory.DATABASE

    assert tool.permissions[0].name == "read_customer_data"


def test_is_frozen() -> None:

    tool = ToolDefinition(name="check_policy_status", version="1.0.0")

    with pytest.raises(Exception):
        tool.name = "changed"