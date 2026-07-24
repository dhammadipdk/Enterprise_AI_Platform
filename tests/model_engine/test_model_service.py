import pytest

from enterprise_ai_platform.model_engine import (
    BaseModelAdapter,
    ModelCapability,
    ModelDefinition,
    ModelResponse,
    ModelService,
    ProviderDefinition,
)


class _FakeChatAdapter(BaseModelAdapter):
    """
    Deterministic fake adapter for tests -- no network, no real
    provider. Echoes the prompt back so tests can assert on exact
    content without depending on any real model's output.
    """

    def invoke(self, request, model):

        return ModelResponse(
            request_id=request.request_id,
            text=f"Echo from {model.name}: {request.prompt}",
            token_usage={
                "input_tokens": len(request.prompt.split()),
                "output_tokens": 5,
            },
            cost=0.0,
            latency_seconds=0.01,
        )


def _register_anthropic(service: ModelService) -> None:

    service.register_provider(
        ProviderDefinition(name="anthropic", description="Anthropic API"),
        _FakeChatAdapter(),
    )


def test_register_provider_makes_it_discoverable() -> None:

    service = ModelService()

    assert not service.provider_exists("anthropic")

    _register_anthropic(service)

    assert service.provider_exists("anthropic")

    assert service.list_providers() == ["anthropic"]

    assert service.get_provider_definition("anthropic").description == (
        "Anthropic API"
    )


def test_get_provider_definition_missing_raises_key_error() -> None:

    service = ModelService()

    with pytest.raises(KeyError):
        service.get_provider_definition("does_not_exist")


def test_register_model_without_provider_raises() -> None:

    service = ModelService()

    model = ModelDefinition(
        name="claude-sonnet-5", version="1.0.0", provider="anthropic"
    )

    with pytest.raises(ValueError, match="anthropic"):
        service.register_model(model)


def test_register_model_after_provider_succeeds() -> None:

    service = ModelService()

    _register_anthropic(service)

    model = ModelDefinition(
        name="claude-sonnet-5",
        version="1.0.0",
        provider="anthropic",
        capabilities=[ModelCapability.CHAT],
    )

    service.register_model(model)

    assert service.model_exists("claude-sonnet-5")


def test_get_model_missing_raises_key_error() -> None:

    service = ModelService()

    with pytest.raises(KeyError):
        service.get_model("does_not_exist")


def test_get_model_specific_version() -> None:

    service = ModelService()

    _register_anthropic(service)

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="1.0.0", provider="anthropic")
    )

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="2.0.0", provider="anthropic")
    )

    model = service.get_model("claude-sonnet-5", version="1.0.0")

    assert model.version == "1.0.0"


def test_get_model_default_returns_latest_version() -> None:

    service = ModelService()

    _register_anthropic(service)

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="1.0.0", provider="anthropic")
    )

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="2.0.0", provider="anthropic")
    )

    model = service.get_model("claude-sonnet-5")

    assert model.version == "2.0.0"


def test_get_model_latest_uses_numeric_not_string_comparison() -> None:

    service = ModelService()

    _register_anthropic(service)

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="1.9.0", provider="anthropic")
    )

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="1.10.0", provider="anthropic")
    )

    model = service.get_model("claude-sonnet-5")

    assert model.version == "1.10.0"


def test_list_models_returns_unique_names() -> None:

    service = ModelService()

    _register_anthropic(service)

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="1.0.0", provider="anthropic")
    )

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="2.0.0", provider="anthropic")
    )

    service.register_model(
        ModelDefinition(name="claude-haiku", version="1.0.0", provider="anthropic")
    )

    assert service.list_models() == ["claude-haiku", "claude-sonnet-5"]


def test_list_models_filtered_by_capability() -> None:

    service = ModelService()

    _register_anthropic(service)

    service.register_model(
        ModelDefinition(
            name="claude-sonnet-5",
            version="1.0.0",
            provider="anthropic",
            capabilities=[ModelCapability.CHAT, ModelCapability.REASONING],
        )
    )

    service.register_model(
        ModelDefinition(
            name="embed-model",
            version="1.0.0",
            provider="anthropic",
            capabilities=[ModelCapability.EMBEDDING],
        )
    )

    assert service.list_models(capability=ModelCapability.EMBEDDING) == [
        "embed-model"
    ]

    assert service.list_models(capability=ModelCapability.CHAT) == [
        "claude-sonnet-5"
    ]


def test_list_versions_sorted_numerically() -> None:

    service = ModelService()

    _register_anthropic(service)

    for version in ["1.9.0", "1.2.0", "1.10.0"]:
        service.register_model(
            ModelDefinition(
                name="claude-sonnet-5", version=version, provider="anthropic"
            )
        )

    assert service.list_versions("claude-sonnet-5") == [
        "1.2.0",
        "1.9.0",
        "1.10.0",
    ]


def test_execute_dispatches_to_registered_adapter() -> None:

    service = ModelService()

    _register_anthropic(service)

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="1.0.0", provider="anthropic")
    )

    response = service.execute(
        "claude-sonnet-5", "Zero dep matlab kya hai?"
    )

    assert response.text == (
        "Echo from claude-sonnet-5: Zero dep matlab kya hai?"
    )

    assert response.token_usage["output_tokens"] == 5


def test_execute_uses_latest_version_by_default() -> None:

    service = ModelService()

    _register_anthropic(service)

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="1.0.0", provider="anthropic")
    )

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="2.0.0", provider="anthropic")
    )

    response = service.execute("claude-sonnet-5", "hi")

    assert "claude-sonnet-5" in response.text


def test_health_reflects_provider_registration() -> None:

    service = ModelService()

    assert not service.health("anthropic")

    _register_anthropic(service)

    assert service.health("anthropic")


def test_lifecycle_transitions() -> None:

    service = ModelService()

    service.initialize()

    service.start()

    assert service.is_running

    service.stop()

    service.dispose()


def test_dispose_clears_providers_and_models() -> None:

    service = ModelService()

    _register_anthropic(service)

    service.register_model(
        ModelDefinition(name="claude-sonnet-5", version="1.0.0", provider="anthropic")
    )

    service.initialize()

    service.start()

    service.stop()

    service.dispose()

    assert not service.provider_exists("anthropic")

    assert not service.model_exists("claude-sonnet-5")