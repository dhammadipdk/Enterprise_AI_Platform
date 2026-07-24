import sys
from unittest.mock import MagicMock

import pytest

from enterprise_ai_platform.model_engine import (
    ModelDefinition,
    ModelRequest,
)
from enterprise_ai_platform.model_engine.adapters import AnthropicAdapter


def _model(configuration=None):

    return ModelDefinition(
        name="claude-sonnet-5",
        version="1.0.0",
        provider="anthropic",
        configuration=configuration or {},
    )


def _fake_response(text, input_tokens, output_tokens):

    block = MagicMock()

    block.type = "text"

    block.text = text

    response = MagicMock()

    response.content = [block]

    response.usage.input_tokens = input_tokens

    response.usage.output_tokens = output_tokens

    return response


def test_invoke_parses_response_correctly() -> None:

    adapter = AnthropicAdapter(api_key="sk-fake-key")

    fake_client = MagicMock()

    fake_client.messages.create.return_value = _fake_response(
        "Zero dep covers full part cost.", 15, 9
    )

    adapter._client = fake_client

    request = ModelRequest(prompt="Zero dep matlab kya hai?")

    response = adapter.invoke(request, _model())

    assert response.text == "Zero dep covers full part cost."

    assert response.token_usage == {"input_tokens": 15, "output_tokens": 9}

    assert response.request_id == request.request_id


def test_invoke_passes_system_prompt_separately() -> None:

    adapter = AnthropicAdapter(api_key="sk-fake-key")

    fake_client = MagicMock()

    fake_client.messages.create.return_value = _fake_response("hi", 1, 1)

    adapter._client = fake_client

    request = ModelRequest(
        prompt="Zero dep matlab kya hai?",
        system_prompt="You are InsureAI's explanation assistant.",
    )

    adapter.invoke(request, _model())

    call_kwargs = fake_client.messages.create.call_args.kwargs

    assert call_kwargs["system"] == "You are InsureAI's explanation assistant."

    assert call_kwargs["messages"] == [
        {"role": "user", "content": "Zero dep matlab kya hai?"}
    ]


def test_invoke_uses_configured_model_name_override() -> None:

    adapter = AnthropicAdapter(api_key="sk-fake-key")

    fake_client = MagicMock()

    fake_client.messages.create.return_value = _fake_response("hi", 1, 1)

    adapter._client = fake_client

    model = _model(configuration={"anthropic_model_name": "claude-haiku-5"})

    adapter.invoke(ModelRequest(prompt="hi"), model)

    call_kwargs = fake_client.messages.create.call_args.kwargs

    assert call_kwargs["model"] == "claude-haiku-5"


def test_invoke_wraps_client_errors_with_context() -> None:

    adapter = AnthropicAdapter(api_key="sk-fake-key")

    fake_client = MagicMock()

    fake_client.messages.create.side_effect = ConnectionError("timeout")

    adapter._client = fake_client

    with pytest.raises(RuntimeError, match="Anthropic request failed"):
        adapter.invoke(ModelRequest(prompt="hi"), _model())


def test_missing_api_key_raises_clear_error(monkeypatch) -> None:

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    adapter = AnthropicAdapter()

    with pytest.raises(RuntimeError, match="No Anthropic API key configured"):
        adapter.invoke(ModelRequest(prompt="hi"), _model())


def test_get_client_reads_key_from_environment_variable(monkeypatch) -> None:
    """
    Exercises the real _get_client() code path (not just the "missing
    key raises" branch), by stubbing sys.modules["anthropic"] with a
    fake module so the lazy `import anthropic` succeeds without the
    real package installed. Confirms the env var is actually read and
    passed through to the client constructor.
    """

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env-key")

    fake_anthropic_module = MagicMock()

    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic_module)

    adapter = AnthropicAdapter()

    client = adapter._get_client()

    fake_anthropic_module.Anthropic.assert_called_once_with(
        api_key="sk-env-key"
    )

    assert client is fake_anthropic_module.Anthropic.return_value

    # Second call must reuse the cached client, not construct again.
    adapter._get_client()

    fake_anthropic_module.Anthropic.assert_called_once()


def test_explicit_api_key_takes_precedence_over_environment(
    monkeypatch,
) -> None:

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env-key")

    fake_anthropic_module = MagicMock()

    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic_module)

    adapter = AnthropicAdapter(api_key="sk-explicit-key")

    adapter._get_client()

    fake_anthropic_module.Anthropic.assert_called_once_with(
        api_key="sk-explicit-key"
    )