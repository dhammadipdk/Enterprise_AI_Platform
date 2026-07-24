import sys
from unittest.mock import MagicMock

import pytest

from enterprise_ai_platform.model_engine import (
    ModelDefinition,
    ModelRequest,
)
from enterprise_ai_platform.model_engine.adapters import OpenAIAdapter


def _model(configuration=None):

    return ModelDefinition(
        name="gpt-4o-mini",
        version="1.0.0",
        provider="openai",
        configuration=configuration or {},
    )


def _fake_response(text, prompt_tokens, completion_tokens):

    response = MagicMock()

    response.choices = [MagicMock()]

    response.choices[0].message.content = text

    response.usage.prompt_tokens = prompt_tokens

    response.usage.completion_tokens = completion_tokens

    return response


def test_invoke_parses_response_correctly() -> None:

    adapter = OpenAIAdapter(api_key="sk-fake-key")

    fake_client = MagicMock()

    fake_client.chat.completions.create.return_value = _fake_response(
        "Zero dep covers full part cost.", 14, 7
    )

    adapter._client = fake_client

    request = ModelRequest(prompt="Zero dep matlab kya hai?")

    response = adapter.invoke(request, _model())

    assert response.text == "Zero dep covers full part cost."

    assert response.token_usage == {"input_tokens": 14, "output_tokens": 7}

    assert response.request_id == request.request_id


def test_invoke_includes_system_prompt_in_messages() -> None:

    adapter = OpenAIAdapter(api_key="sk-fake-key")

    fake_client = MagicMock()

    fake_client.chat.completions.create.return_value = _fake_response(
        "hi", 1, 1
    )

    adapter._client = fake_client

    request = ModelRequest(
        prompt="Zero dep matlab kya hai?",
        system_prompt="You are InsureAI's explanation assistant.",
    )

    adapter.invoke(request, _model())

    call_kwargs = fake_client.chat.completions.create.call_args.kwargs

    assert call_kwargs["messages"][0] == {
        "role": "system",
        "content": "You are InsureAI's explanation assistant.",
    }

    assert call_kwargs["messages"][1] == {
        "role": "user",
        "content": "Zero dep matlab kya hai?",
    }


def test_invoke_uses_configured_model_name_override() -> None:

    adapter = OpenAIAdapter(api_key="sk-fake-key")

    fake_client = MagicMock()

    fake_client.chat.completions.create.return_value = _fake_response(
        "hi", 1, 1
    )

    adapter._client = fake_client

    model = _model(configuration={"openai_model_name": "gpt-4o"})

    adapter.invoke(ModelRequest(prompt="hi"), model)

    call_kwargs = fake_client.chat.completions.create.call_args.kwargs

    assert call_kwargs["model"] == "gpt-4o"


def test_invoke_wraps_client_errors_with_context() -> None:

    adapter = OpenAIAdapter(api_key="sk-fake-key")

    fake_client = MagicMock()

    fake_client.chat.completions.create.side_effect = ConnectionError(
        "timeout"
    )

    adapter._client = fake_client

    with pytest.raises(RuntimeError, match="OpenAI request failed"):
        adapter.invoke(ModelRequest(prompt="hi"), _model())


def test_missing_api_key_raises_clear_error(monkeypatch) -> None:

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    adapter = OpenAIAdapter()

    with pytest.raises(RuntimeError, match="No OpenAI API key configured"):
        adapter.invoke(ModelRequest(prompt="hi"), _model())


def test_get_client_reads_key_from_environment_variable(monkeypatch) -> None:

    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")

    fake_openai_module = MagicMock()

    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)

    adapter = OpenAIAdapter()

    client = adapter._get_client()

    fake_openai_module.OpenAI.assert_called_once_with(api_key="sk-env-key")

    assert client is fake_openai_module.OpenAI.return_value

    adapter._get_client()

    fake_openai_module.OpenAI.assert_called_once()


def test_explicit_api_key_takes_precedence_over_environment(
    monkeypatch,
) -> None:

    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")

    fake_openai_module = MagicMock()

    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)

    adapter = OpenAIAdapter(api_key="sk-explicit-key")

    adapter._get_client()

    fake_openai_module.OpenAI.assert_called_once_with(
        api_key="sk-explicit-key"
    )