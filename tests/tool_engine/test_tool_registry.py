import pytest

from enterprise_ai_platform.tool_engine import ToolDefinition, ToolRegistry


def _tool(name="check_policy_status", version="1.0.0"):

    return ToolDefinition(name=name, version=version)


def test_register_and_get() -> None:

    registry = ToolRegistry()

    registry.register("check_policy_status@1.0.0", _tool())

    retrieved = registry.get("check_policy_status@1.0.0")

    assert retrieved.name == "check_policy_status"


def test_get_missing_raises_key_error() -> None:

    registry = ToolRegistry()

    with pytest.raises(KeyError):
        registry.get("does_not_exist@1.0.0")


def test_clear_removes_everything() -> None:

    registry = ToolRegistry()

    registry.register("check_policy_status@1.0.0", _tool())

    registry.clear()

    assert registry.names() == []