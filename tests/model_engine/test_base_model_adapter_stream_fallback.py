from enterprise_ai_platform.model_engine import (
    BaseModelAdapter,
    ModelDefinition,
    ModelRequest,
    ModelResponse,
)


class _InvokeOnlyAdapter(BaseModelAdapter):
    """
    Deliberately implements ONLY invoke() -- never overrides stream()
    -- to verify BaseModelAdapter's default fallback behavior works
    without every adapter needing to implement streaming itself.
    """

    def invoke(self, request, model):

        return ModelResponse(
            request_id=request.request_id,
            text="Zero dep covers full part cost.",
        )


def test_default_stream_yields_single_final_chunk_matching_invoke() -> None:

    adapter = _InvokeOnlyAdapter()

    model = ModelDefinition(name="test-model", version="1.0.0", provider="test")

    request = ModelRequest(prompt="Zero dep matlab kya hai?")

    chunks = list(adapter.stream(request, model))

    assert len(chunks) == 1

    assert chunks[0].is_final is True

    assert chunks[0].text == "Zero dep covers full part cost."

    assert chunks[0].request_id == request.request_id


def test_stream_is_lazy_until_iterated() -> None:

    calls = []

    class _TrackedAdapter(BaseModelAdapter):

        def invoke(self, request, model):
            calls.append("invoked")
            return ModelResponse(request_id=request.request_id, text="hi")

    adapter = _TrackedAdapter()

    model = ModelDefinition(name="test-model", version="1.0.0", provider="test")

    generator = adapter.stream(ModelRequest(prompt="hi"), model)

    assert calls == []  # nothing has run yet, just constructing the generator

    next(generator)

    assert calls == ["invoked"]