from unittest.mock import MagicMock

import pytest

from enterprise_ai_platform.model_engine import (
    ModelDefinition,
    ModelRequest,
)
from enterprise_ai_platform.model_engine.adapters import OllamaAdapter


def _model(configuration=None):

    return ModelDefinition(
        name="llama3.2:3b",
        version="1.0.0",
        provider="ollama",
        configuration=configuration or {},
    )


def test_invoke_parses_response_correctly() -> None:

    adapter = OllamaAdapter()

    fake_client = MagicMock()

    fake_client.chat.return_value = {
        "message": {
            "role": "assistant",
            "content": "Zero dep covers full part cost.",
        },
        "prompt_eval_count": 12,
        "eval_count": 8,
    }

    adapter._client = fake_client

    request = ModelRequest(prompt="Zero dep matlab kya hai?")

    response = adapter.invoke(request, _model())

    assert response.text == "Zero dep covers full part cost."

    assert response.token_usage == {"input_tokens": 12, "output_tokens": 8}

    assert response.cost == 0.0

    assert response.request_id == request.request_id


def test_invoke_includes_system_prompt_in_messages() -> None:

    adapter = OllamaAdapter()

    fake_client = MagicMock()

    fake_client.chat.return_value = {
        "message": {"content": "hi"},
    }

    adapter._client = fake_client

    request = ModelRequest(
        prompt="Zero dep matlab kya hai?",
        system_prompt="You are InsureAI's explanation assistant.",
    )

    adapter.invoke(request, _model())

    call_kwargs = fake_client.chat.call_args.kwargs

    assert call_kwargs["messages"][0] == {
        "role": "system",
        "content": "You are InsureAI's explanation assistant.",
    }

    assert call_kwargs["messages"][1] == {
        "role": "user",
        "content": "Zero dep matlab kya hai?",
    }


def test_invoke_uses_configured_model_name_override() -> None:

    adapter = OllamaAdapter()

    fake_client = MagicMock()

    fake_client.chat.return_value = {"message": {"content": "hi"}}

    adapter._client = fake_client

    model = _model(configuration={"ollama_model_name": "llama3.2:1b"})

    adapter.invoke(ModelRequest(prompt="hi"), model)

    call_kwargs = fake_client.chat.call_args.kwargs

    assert call_kwargs["model"] == "llama3.2:1b"


def test_invoke_wraps_client_errors_with_context() -> None:

    adapter = OllamaAdapter()

    fake_client = MagicMock()

    fake_client.chat.side_effect = ConnectionError("connection refused")

    adapter._client = fake_client

    with pytest.raises(RuntimeError, match="Ollama request failed"):
        adapter.invoke(ModelRequest(prompt="hi"), _model())


def test_client_construction_is_lazy() -> None:

    adapter = OllamaAdapter()

    assert adapter._client is None
    
def test_stream_yields_incremental_chunks() -> None:

    adapter = OllamaAdapter()

    fake_client = MagicMock()

    fake_client.chat.return_value = iter(
        [
            {"message": {"content": "Zero "}, "done": False},
            {"message": {"content": "dep "}, "done": False},
            {
                "message": {"content": "covers cost."},
                "done": True,
                "prompt_eval_count": 10,
                "eval_count": 3,
            },
        ]
    )

    adapter._client = fake_client

    request = ModelRequest(prompt="Zero dep matlab kya hai?")

    chunks = list(adapter.stream(request, _model()))

    assert len(chunks) == 3

    assert [c.text for c in chunks] == ["Zero ", "dep ", "covers cost."]

    assert [c.is_final for c in chunks] == [False, False, True]

    assert chunks[-1].metadata == {"prompt_eval_count": 10, "eval_count": 3}

    assert chunks[0].metadata == {}


def test_stream_reassembled_text_matches_full_response() -> None:

    adapter = OllamaAdapter()

    fake_client = MagicMock()

    fake_client.chat.return_value = iter(
        [
            {"message": {"content": "Zero "}, "done": False},
            {"message": {"content": "dep covers cost."}, "done": True},
        ]
    )

    adapter._client = fake_client

    chunks = list(adapter.stream(ModelRequest(prompt="hi"), _model()))

    full_text = "".join(chunk.text for chunk in chunks)

    assert full_text == "Zero dep covers cost."


def test_stream_passes_stream_true_to_client() -> None:

    adapter = OllamaAdapter()

    fake_client = MagicMock()

    fake_client.chat.return_value = iter(
        [{"message": {"content": "hi"}, "done": True}]
    )

    adapter._client = fake_client

    list(adapter.stream(ModelRequest(prompt="hi"), _model()))

    call_kwargs = fake_client.chat.call_args.kwargs

    assert call_kwargs["stream"] is True


def test_stream_all_requests_share_the_request_id() -> None:

    adapter = OllamaAdapter()

    fake_client = MagicMock()

    fake_client.chat.return_value = iter(
        [
            {"message": {"content": "a"}, "done": False},
            {"message": {"content": "b"}, "done": True},
        ]
    )

    adapter._client = fake_client

    request = ModelRequest(prompt="hi")

    chunks = list(adapter.stream(request, _model()))

    assert all(chunk.request_id == request.request_id for chunk in chunks)