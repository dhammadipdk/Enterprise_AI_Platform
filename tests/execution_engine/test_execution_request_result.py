from enterprise_ai_platform.execution_engine import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionUnitState,
)


def test_request_auto_generates_id() -> None:

    request = ExecutionRequest()

    assert request.request_id

    assert request.priority == 0

    assert request.deadline is None


def test_request_ids_are_unique() -> None:

    a = ExecutionRequest()

    b = ExecutionRequest()

    assert a.request_id != b.request_id


def test_result_defaults() -> None:

    result = ExecutionResult(
        request_id="r1",
        unit_name="calculate_premium",
        state=ExecutionUnitState.QUEUED,
    )

    assert result.result is None

    assert result.error is None

    assert result.attempts == 0