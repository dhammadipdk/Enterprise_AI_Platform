import pytest

from enterprise_ai_platform.model_engine import ModelDefinition, ModelRegistry


def _model(name="claude-sonnet-5", version="1.0.0"):

    return ModelDefinition(name=name, version=version, provider="anthropic")


def test_register_and_get() -> None:

    registry = ModelRegistry()

    registry.register("claude-sonnet-5@1.0.0", _model())

    retrieved = registry.get("claude-sonnet-5@1.0.0")

    assert retrieved.name == "claude-sonnet-5"


def test_get_missing_raises_key_error() -> None:

    registry = ModelRegistry()

    with pytest.raises(KeyError):
        registry.get("does_not_exist@1.0.0")


def test_clear_removes_everything() -> None:

    registry = ModelRegistry()

    registry.register("claude-sonnet-5@1.0.0", _model())

    registry.clear()

    assert registry.names() == []