import pytest

from enterprise_ai_platform.model_engine import ModelCapability, ModelDefinition


def test_defaults() -> None:

    model = ModelDefinition(name="claude-sonnet-5", version="1.0.0", provider="anthropic")

    assert model.family is None

    assert model.capabilities == []

    assert model.limits == {}

    assert model.configuration == {}

    assert model.metadata == {}


def test_full_definition() -> None:

    model = ModelDefinition(
        name="claude-sonnet-5",
        version="1.0.0",
        provider="anthropic",
        family="claude",
        capabilities=[ModelCapability.CHAT, ModelCapability.REASONING],
        limits={"context_window": 200000},
        configuration={"temperature": 0.7},
        metadata={"tier": "primary"},
    )

    assert ModelCapability.CHAT in model.capabilities

    assert model.limits["context_window"] == 200000


def test_is_frozen() -> None:

    model = ModelDefinition(name="claude-sonnet-5", version="1.0.0", provider="anthropic")

    with pytest.raises(Exception):
        model.provider = "openai" 