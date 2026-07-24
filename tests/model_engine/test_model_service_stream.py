from enterprise_ai_platform.model_engine import (
    BaseModelAdapter,
    ModelDefinition,
    ModelResponse,
    ModelService,
    ProviderDefinition,
    StreamChunk,
)


class _FakeStreamingAdapter(BaseModelAdapter):
    """
    Fake adapter that genuinely overrides stream() with multiple
    chunks, to verify ModelService.stream() passes them through
    correctly rather than buffering or collapsing them.
    """

    def invoke(self, request, model):

        return ModelResponse(request_id=request.request_id, text="hi")

    def stream(self, request, model):

        yield StreamChunk(request_id=request.request_id, text="Zero ")

        yield StreamChunk(request_id=request.request_id, text="dep ")

        yield StreamChunk(
            request_id=request.request_id,
            text="covers cost.",
            is_final=True,
        )


def _service() -> ModelService:

    service = ModelService()

    service.register_provider(
        ProviderDefinition(name="ollama", description="Local Ollama"),
        _FakeStreamingAdapter(),
    )

    service.register_model(
        ModelDefinition(name="explanation_model", version="1.0.0", provider="ollama")
    )

    return service


def test_stream_passes_through_all_chunks_in_order() -> None:

    service = _service()

    chunks = list(
        service.stream("explanation_model", "Zero dep matlab kya hai?")
    )

    assert [c.text for c in chunks] == ["Zero ", "dep ", "covers cost."]

    assert chunks[-1].is_final is True


def test_stream_uses_latest_version_by_default() -> None:

    service = _service()

    service.register_model(
        ModelDefinition(
            name="explanation_model", version="2.0.0", provider="ollama"
        )
    )

    chunks = list(service.stream("explanation_model", "hi"))

    assert len(chunks) == 3


def test_stream_is_lazy() -> None:

    service = _service()

    generator = service.stream("explanation_model", "hi")

    # Constructing the generator should not raise even though nothing
    # has been consumed yet.
    first_chunk = next(generator)

    assert first_chunk.text == "Zero "