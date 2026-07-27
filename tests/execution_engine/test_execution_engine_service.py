import time
from datetime import datetime, timedelta, timezone

import pytest

from enterprise_ai_platform.execution_engine import (
    ExecutionDefinition,
    ExecutionEngineService,
    ExecutionRequest,
    ExecutionRetryPolicy,
    ExecutionUnit,
    ExecutionUnitState,
    RetryStrategy,
    SchedulingPolicy,
)


def _unit(name="calculate_premium", func=None, **definition_kwargs):

    return ExecutionUnit(
        definition=ExecutionDefinition(name=name, **definition_kwargs),
        func=func or (lambda: "done"),
    )


def test_submit_queues_without_executing() -> None:

    service = ExecutionEngineService()

    calls = []

    request_id = service.submit(_unit(func=lambda: calls.append(1)))

    assert service.queue_length() == 1

    assert calls == []  # nothing executed yet

    assert service.status(request_id).state == ExecutionUnitState.QUEUED


def test_run_next_executes_and_returns_result() -> None:

    service = ExecutionEngineService()

    service.submit(_unit(func=lambda: "Zero dep covers full part cost."))

    result = service.run_next()

    assert result.state == ExecutionUnitState.COMPLETED

    assert result.result == "Zero dep covers full part cost."

    assert result.attempts == 1

    assert result.duration_seconds is not None

    assert service.queue_length() == 0


def test_run_next_on_empty_queue_returns_none() -> None:

    service = ExecutionEngineService()

    assert service.run_next() is None


def test_run_all_drains_entire_queue() -> None:

    service = ExecutionEngineService()

    service.submit(_unit(name="a", func=lambda: "a-result"))

    service.submit(_unit(name="b", func=lambda: "b-result"))

    results = service.run_all()

    assert len(results) == 2

    assert service.queue_length() == 0

    assert {r.result for r in results} == {"a-result", "b-result"}


def test_fifo_scheduling_runs_in_submission_order() -> None:

    service = ExecutionEngineService(scheduling_policy=SchedulingPolicy.FIFO)

    order = []

    service.submit(_unit(name="first", func=lambda: order.append("first")))

    service.submit(_unit(name="second", func=lambda: order.append("second")))

    service.run_all()

    assert order == ["first", "second"]


def test_priority_scheduling_runs_highest_priority_first() -> None:

    service = ExecutionEngineService(
        scheduling_policy=SchedulingPolicy.PRIORITY
    )

    order = []

    service.submit(
        _unit(name="low", func=lambda: order.append("low")),
        request=ExecutionRequest(priority=1),
    )

    service.submit(
        _unit(name="high", func=lambda: order.append("high")),
        request=ExecutionRequest(priority=10),
    )

    service.run_all()

    assert order == ["high", "low"]


def test_deadline_scheduling_runs_earliest_deadline_first() -> None:

    service = ExecutionEngineService(
        scheduling_policy=SchedulingPolicy.DEADLINE
    )

    now = datetime.now(timezone.utc)

    order = []

    service.submit(
        _unit(name="later", func=lambda: order.append("later")),
        request=ExecutionRequest(deadline=now + timedelta(hours=2)),
    )

    service.submit(
        _unit(name="soonest", func=lambda: order.append("soonest")),
        request=ExecutionRequest(deadline=now + timedelta(minutes=5)),
    )

    service.run_all()

    assert order == ["soonest", "later"]


def test_failure_without_retry_policy_reports_failed() -> None:

    service = ExecutionEngineService()

    def _always_fails():
        raise RuntimeError("simulated permanent failure")

    service.submit(_unit(func=_always_fails))

    result = service.run_next()

    assert result.state == ExecutionUnitState.FAILED

    assert result.attempts == 1

    assert "simulated permanent failure" in result.error


def test_retry_policy_succeeds_after_transient_failures() -> None:

    service = ExecutionEngineService()

    call_count = {"n": 0}

    def _flaky():
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise RuntimeError(f"transient failure #{call_count['n']}")
        return "succeeded on attempt 3"

    service.submit(
        _unit(
            func=_flaky,
            retry_policy=ExecutionRetryPolicy(
                strategy=RetryStrategy.FIXED,
                max_attempts=3,
                base_delay_seconds=0.01,
            ),
        )
    )

    result = service.run_next()

    assert result.state == ExecutionUnitState.COMPLETED

    assert result.attempts == 3

    assert result.result == "succeeded on attempt 3"


def test_retry_policy_exhausted_reports_failed_with_attempt_count() -> None:

    service = ExecutionEngineService()

    def _always_fails():
        raise RuntimeError("permanent failure")

    service.submit(
        _unit(
            func=_always_fails,
            retry_policy=ExecutionRetryPolicy(
                strategy=RetryStrategy.FIXED,
                max_attempts=3,
                base_delay_seconds=0.01,
            ),
        )
    )

    result = service.run_next()

    assert result.state == ExecutionUnitState.FAILED

    assert result.attempts == 3


def test_genuine_timeout_returns_control_before_slow_function_finishes() -> None:

    service = ExecutionEngineService()

    def _slow_function():
        time.sleep(5.0)
        return "should never be seen"

    service.submit(_unit(func=_slow_function, timeout_seconds=0.2))

    start = time.monotonic()

    result = service.run_next()

    elapsed = time.monotonic() - start

    assert result.state == ExecutionUnitState.TIMED_OUT

    assert elapsed < 1.0  # genuinely got control back, not after the full 5s sleep


def test_cancel_before_run_marks_cancelled() -> None:

    service = ExecutionEngineService()

    calls = []

    request_id = service.submit(_unit(func=lambda: calls.append(1)))

    service.cancel(request_id)

    result = service.run_next()

    assert result.state == ExecutionUnitState.CANCELLED

    assert calls == []  # never actually executed


def test_retry_reruns_a_previous_execution() -> None:

    service = ExecutionEngineService()

    call_count = {"n": 0}

    def _func():
        call_count["n"] += 1
        return f"call {call_count['n']}"

    request_id = service.submit(_unit(func=_func))

    first_result = service.run_next()

    assert first_result.result == "call 1"

    retried_result = service.retry(request_id)

    assert retried_result.result == "call 2"

    assert service.status(request_id).result == "call 2"


def test_retry_missing_request_id_raises_key_error() -> None:

    service = ExecutionEngineService()

    with pytest.raises(KeyError):
        service.retry("does_not_exist")


def test_status_missing_request_id_raises_key_error() -> None:

    service = ExecutionEngineService()

    with pytest.raises(KeyError):
        service.status("does_not_exist")


def test_history_returns_all_results() -> None:

    service = ExecutionEngineService()

    service.submit(_unit(name="a", func=lambda: "a"))

    service.submit(_unit(name="b", func=lambda: "b"))

    service.run_all()

    assert len(service.history()) == 2


def test_metrics_counts_by_state() -> None:

    service = ExecutionEngineService()

    service.submit(_unit(func=lambda: "ok"))

    def _fails():
        raise RuntimeError("boom")

    service.submit(_unit(func=_fails))

    service.run_all()

    metrics = service.metrics()

    assert metrics["completed"] == 1

    assert metrics["failed"] == 1

    assert metrics["queue_length"] == 0


def test_health_is_always_true() -> None:

    service = ExecutionEngineService()

    assert service.health() is True


def test_lifecycle_transitions() -> None:

    service = ExecutionEngineService()

    service.initialize()

    service.start()

    assert service.is_running

    service.stop()

    service.dispose()


def test_dispose_clears_queue_and_history() -> None:

    service = ExecutionEngineService()

    service.submit(_unit(func=lambda: "ok"))

    service.initialize()

    service.start()

    service.stop()

    service.dispose()

    assert service.queue_length() == 0

    assert service.history() == []