from enterprise_ai_platform.tool_engine import ToolRequest, ToolResponse


def test_request_auto_generates_id() -> None:

    request = ToolRequest(tool_name="check_policy_status")

    assert request.request_id

    assert request.parameters == {}

    assert request.priority == 0


def test_request_ids_are_unique() -> None:

    a = ToolRequest(tool_name="check_policy_status")

    b = ToolRequest(tool_name="check_policy_status")

    assert a.request_id != b.request_id


def test_response_defaults() -> None:

    response = ToolResponse(request_id="r1", status="success")

    assert response.result is None

    assert response.error is None

    assert response.artifacts == []

    assert response.execution_time_seconds is None