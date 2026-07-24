import pytest

from enterprise_ai_platform.model_engine import (
    BaseModelAdapter,
    ModelDefinition,
    ModelResponse,
    ModelService,
    ProviderDefinition,
)


class _FakeJSONAdapter(BaseModelAdapter):
    """
    Fake adapter returning a fixed, possibly-messy JSON string so
    execute()'s structured output handling can be tested end-to-end
    without a real provider.
    """

    def __init__(self, canned_text: str) -> None:

        self._canned_text = canned_text

        self.last_request = None

    def invoke(self, request, model):

        self.last_request = request

        return ModelResponse(
            request_id=request.request_id,
            text=self._canned_text,
        )


def _service_with_model(canned_text: str) -> tuple[ModelService, _FakeJSONAdapter]:

    service = ModelService()

    adapter = _FakeJSONAdapter(canned_text)

    service.register_provider(
        ProviderDefinition(name="ollama", description="Local Ollama"), adapter
    )

    service.register_model(
        ModelDefinition(name="explanation_model", version="1.0.0", provider="ollama")
    )

    return service, adapter


_SCHEMA = {
    "type": "object",
    "properties": {"explanation": {"type": "string"}},
    "required": ["explanation"],
}


def test_execute_without_schema_leaves_structured_output_none() -> None:

    service, _ = _service_with_model("Zero dep covers full part cost.")

    response = service.execute("explanation_model", "Zero dep matlab kya hai?")

    assert response.structured_output is None


def test_execute_with_schema_populates_structured_output() -> None:

    service, _ = _service_with_model(
        '{"explanation": "Zero dep covers full part cost."}'
    )

    response = service.execute(
        "explanation_model",
        "Zero dep matlab kya hai?",
        response_schema=_SCHEMA,
    )

    assert response.structured_output == {
        "explanation": "Zero dep covers full part cost."
    }


def test_execute_with_schema_handles_markdown_fenced_output() -> None:

    service, _ = _service_with_model(
        '```json\n{"explanation": "Zero dep covers full part cost."}\n```'
    )

    response = service.execute(
        "explanation_model",
        "Zero dep matlab kya hai?",
        response_schema=_SCHEMA,
    )

    assert response.structured_output == {
        "explanation": "Zero dep covers full part cost."
    }


def test_execute_with_schema_augments_the_prompt_sent_to_the_adapter() -> None:

    service, adapter = _service_with_model(
        '{"explanation": "hi"}'
    )

    service.execute(
        "explanation_model",
        "Zero dep matlab kya hai?",
        response_schema=_SCHEMA,
    )

    assert "Zero dep matlab kya hai?" in adapter.last_request.prompt

    assert "JSON" in adapter.last_request.prompt

    assert adapter.last_request.response_schema == _SCHEMA


def test_execute_with_schema_raises_on_non_conforming_output() -> None:

    service, _ = _service_with_model("I cannot help with that.")

    with pytest.raises(ValueError, match="Could not extract valid JSON"):
        service.execute(
            "explanation_model",
            "Zero dep matlab kya hai?",
            response_schema=_SCHEMA,
        )


def test_execute_with_schema_raises_on_schema_mismatch() -> None:

    service, _ = _service_with_model('{"wrong_key": "hi"}')

    with pytest.raises(ValueError, match="did not match the required schema"):
        service.execute(
            "explanation_model",
            "Zero dep matlab kya hai?",
            response_schema=_SCHEMA,
        )


def test_resolve_schema_rejects_invalid_type() -> None:

    service, _ = _service_with_model("irrelevant")

    with pytest.raises(TypeError, match="JSON schema dict or a pydantic"):
        service.execute(
            "explanation_model",
            "hi",
            response_schema="not a schema",
        )