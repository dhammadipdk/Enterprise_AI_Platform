from enterprise_ai_platform.model_engine import ModelRequest, ModelResponse


def test_request_auto_generates_id() -> None:

    request = ModelRequest(prompt="Zero dep matlab kya hai?")

    assert request.request_id

    assert request.system_prompt is None

    assert request.parameters == {}


def test_request_ids_are_unique() -> None:

    a = ModelRequest(prompt="hi")

    b = ModelRequest(prompt="hi")

    assert a.request_id != b.request_id


def test_response_ties_back_to_request() -> None:

    request = ModelRequest(prompt="Zero dep matlab kya hai?")

    response = ModelResponse(
        request_id=request.request_id,
        text="Zero dep means full part replacement cost is covered.",
    )

    assert response.request_id == request.request_id

    assert response.response_id != request.request_id

    assert response.cost is None

    assert response.latency_seconds is None