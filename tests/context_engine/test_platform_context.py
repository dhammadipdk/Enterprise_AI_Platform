import pytest

from enterprise_ai_platform.context_engine import PlatformContext


def test_defaults() -> None:

    context = PlatformContext()

    assert context.context_id

    assert context.workflow_context == {}

    assert context.knowledge_context == {}

    assert context.memory_context == {}

    assert context.user_context == {}

    assert context.execution_context == {}

    assert context.tool_context == {}

    assert context.model_context == {}


def test_is_frozen() -> None:

    context = PlatformContext()

    with pytest.raises(Exception):
        context.workflow_context = {"a": 1}