"""
Execution engine service.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

from enterprise_ai_platform.execution_engine.models import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionRetryPolicy,
    ExecutionUnitState,
    RetryStrategy,
    SchedulingPolicy,
)
from enterprise_ai_platform.execution_engine.units import ExecutionUnit
from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)


class ExecutionEngineService(BaseService):
    """
    Public API of the Execution Engine (frozen spec, Section 19):
    submit, cancel, retry, status, history, metrics, health.

    Single-threaded, synchronous execution model for this task: there
    is no standing ExecutionWorker process consuming a queue in the
    background -- submit() enqueues, and run_next()/run_all() drain
    the queue in the configured SchedulingPolicy order, executing
    each unit inline. Multi-threaded/multi-process/distributed
    execution (Section 17) is explicitly deferred; nothing in the
    spec's V1 scope requires it yet, and it introduces real
    concurrency-safety complexity this task doesn't need to take on.

    Timeouts are enforced for real, not just measured after the fact:
    each unit's callable runs in a background thread, and if it
    doesn't finish within timeout_seconds, the caller gets control
    back immediately while the original call is abandoned running in
    the background (Python has no way to forcibly kill a thread). A
    "timeout" that doesn't actually return control early would be
    misleading and unsafe to rely on for bounding a hanging call.

    Every submitted unit and its request are retained for the
    service's lifetime (until dispose()), not discarded after
    execution -- this is what makes retry() genuinely able to re-run
    a previous execution rather than being a stub. The tradeoff is
    unbounded memory growth with usage; there's no eviction/retention
    policy yet, since nothing in this task's scope calls for one.

    Deliberately not implemented yet:
      - Fair/Weighted/Custom scheduling policies (Section 13).
      - Resource management (CPU/GPU/memory quotas, Section 18) --
        meaningful once there's a real concurrent execution model to
        allocate resources across.
      - Execution events (Section 20, e.g. ExecutionStarted) --
        publishing real events needs an event bus, which doesn't
        exist in this codebase yet.
      - Aggregate metrics() beyond simple counts -- richer statistics
        (throughput, worker utilization) need real usage volume and a
        concurrent execution model to be meaningful.
    """

    def __init__(
        self,
        scheduling_policy: SchedulingPolicy = SchedulingPolicy.FIFO,
    ) -> None:

        super().__init__(name="execution_engine_service")

        self._scheduling_policy = scheduling_policy

        self._queue: list[str] = []

        self._units: dict[str, ExecutionUnit] = {}

        self._requests: dict[str, ExecutionRequest] = {}

        self._results: dict[str, ExecutionResult] = {}

        self._cancelled: set[str] = set()

    def initialize(self) -> None:
        """
        Initialize the service.
        """

        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        """
        Start the service.
        """

        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        """
        Stop the service.
        """

        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        """
        Dispose the service and clear all queued work and history.
        """

        self._queue.clear()

        self._units.clear()

        self._requests.clear()

        self._results.clear()

        self._cancelled.clear()

        self._set_state(ComponentState.DISPOSED)

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    def submit(
        self,
        unit: ExecutionUnit,
        request: ExecutionRequest | None = None,
    ) -> str:
        """
        Queue a unit for execution and return its request_id.

        Does not execute immediately -- call run_next() or run_all()
        to actually drain the queue.
        """

        request = request or ExecutionRequest(priority=unit.definition.priority)

        self._units[request.request_id] = unit

        self._requests[request.request_id] = request

        self._queue.append(request.request_id)

        self._results[request.request_id] = ExecutionResult(
            request_id=request.request_id,
            unit_name=unit.definition.name,
            state=ExecutionUnitState.QUEUED,
        )

        return request.request_id

    def queue_length(self) -> int:
        """
        Return the number of units currently queued (not yet run).
        """

        return len(self._queue)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_next(self) -> ExecutionResult | None:
        """
        Pop and execute the next queued unit according to the
        configured SchedulingPolicy, and return its result.

        Returns None if the queue is empty.
        """

        if not self._queue:
            return None

        request_id = self._pop_next()

        unit = self._units[request_id]

        request = self._requests[request_id]

        if request_id in self._cancelled:
            result = ExecutionResult(
                request_id=request_id,
                unit_name=unit.definition.name,
                state=ExecutionUnitState.CANCELLED,
            )
            self._results[request_id] = result
            return result

        result = self._execute_with_retry_and_timeout(unit, request)

        self._results[request_id] = result

        return result

    def run_all(self) -> list[ExecutionResult]:
        """
        Drain the entire queue, executing each unit in scheduling
        order, and return every result in the order they completed.
        """

        results: list[ExecutionResult] = []

        while self._queue:
            results.append(self.run_next())

        return results

    def retry(self, request_id: str) -> ExecutionResult:
        """
        Re-run a previously executed (or queued) unit using its
        original ExecutionUnit and ExecutionRequest, and return the
        new result (overwriting the previous one under the same
        request_id).
        """

        if request_id not in self._units:
            raise KeyError(
                f"No execution found with request id '{request_id}'."
            )

        unit = self._units[request_id]

        request = self._requests[request_id]

        result = self._execute_with_retry_and_timeout(unit, request)

        self._results[request_id] = result

        return result

    def cancel(self, request_id: str) -> None:
        """
        Cancel a queued (not yet started) execution. Has no effect on
        an execution that has already started or completed.
        """

        self._cancelled.add(request_id)

    # ------------------------------------------------------------------
    # Status / history / metrics
    # ------------------------------------------------------------------

    def status(self, request_id: str) -> ExecutionResult:
        """
        Return the current result/status for a request.
        """

        if request_id not in self._results:
            raise KeyError(f"No execution found with request id '{request_id}'.")

        return self._results[request_id]

    def history(self) -> list[ExecutionResult]:
        """
        Return every tracked execution result.
        """

        return list(self._results.values())

    def metrics(self) -> dict[str, int]:
        """
        Return simple counts by state across all tracked executions.
        """

        counts: dict[str, int] = {}

        for result in self._results.values():
            counts[result.state.value] = counts.get(result.state.value, 0) + 1

        counts["queue_length"] = self.queue_length()

        return counts

    def health(self) -> bool:
        """
        Return True. Always healthy for this in-process, synchronous
        implementation; meaningful once real workers/resources exist
        to check.
        """

        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pop_next(self) -> str:

        if self._scheduling_policy == SchedulingPolicy.FIFO:
            index = 0

        elif self._scheduling_policy == SchedulingPolicy.PRIORITY:
            index = max(
                range(len(self._queue)),
                key=lambda i: (
                    self._requests[self._queue[i]].priority,
                    -i,
                ),
            )

        elif self._scheduling_policy == SchedulingPolicy.DEADLINE:

            def _deadline_key(i: int):
                request = self._requests[self._queue[i]]
                return (
                    request.deadline is None,
                    request.deadline
                    or datetime.max.replace(tzinfo=timezone.utc),
                    i,
                )

            index = min(range(len(self._queue)), key=_deadline_key)

        else:
            index = 0

        request_id = self._queue[index]

        del self._queue[index]

        return request_id

    def _execute_with_retry_and_timeout(
        self,
        unit: ExecutionUnit,
        request: ExecutionRequest,
    ) -> ExecutionResult:

        definition = unit.definition

        retry_policy = definition.retry_policy

        started_at = datetime.now(timezone.utc)

        attempt = 0

        last_error: str | None = None

        max_attempts = max(retry_policy.max_attempts, 1)

        while attempt < max_attempts:

            attempt += 1

            try:
                value, timed_out = self._run_with_timeout(
                    unit.func,
                    definition.timeout_seconds,
                )

                if timed_out:
                    last_error = (
                        f"Execution timed out after "
                        f"{definition.timeout_seconds}s (attempt "
                        f"{attempt})."
                    )

                    if attempt >= max_attempts or (
                        retry_policy.strategy == RetryStrategy.NONE
                    ):
                        return self._build_result(
                            request,
                            definition.name,
                            ExecutionUnitState.TIMED_OUT,
                            None,
                            last_error,
                            attempt,
                            started_at,
                        )

                    time.sleep(
                        self._compute_delay(retry_policy, attempt)
                    )

                    continue

                return self._build_result(
                    request,
                    definition.name,
                    ExecutionUnitState.COMPLETED,
                    value,
                    None,
                    attempt,
                    started_at,
                )

            except Exception as error:

                last_error = str(error)

                if attempt >= max_attempts or (
                    retry_policy.strategy == RetryStrategy.NONE
                ):
                    return self._build_result(
                        request,
                        definition.name,
                        ExecutionUnitState.FAILED,
                        None,
                        last_error,
                        attempt,
                        started_at,
                    )

                time.sleep(self._compute_delay(retry_policy, attempt))

        return self._build_result(
            request,
            definition.name,
            ExecutionUnitState.FAILED,
            None,
            last_error,
            attempt,
            started_at,
        )

    @staticmethod
    def _run_with_timeout(func, timeout_seconds: float | None):

        if timeout_seconds is None:
            return func(), False

        result_container: dict = {}

        error_container: dict = {}

        def _target() -> None:
            try:
                result_container["value"] = func()
            except Exception as error:
                error_container["error"] = error

        thread = threading.Thread(target=_target, daemon=True)

        thread.start()

        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            return None, True

        if "error" in error_container:
            raise error_container["error"]

        return result_container.get("value"), False

    @staticmethod
    def _compute_delay(
        retry_policy: ExecutionRetryPolicy,
        attempt: int,
    ) -> float:

        if retry_policy.strategy == RetryStrategy.NONE:
            delay = 0.0

        elif retry_policy.strategy == RetryStrategy.FIXED:
            delay = retry_policy.base_delay_seconds

        elif retry_policy.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = retry_policy.base_delay_seconds * attempt

        elif retry_policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = retry_policy.base_delay_seconds * (2 ** (attempt - 1))

        else:
            delay = 0.0

        if retry_policy.max_delay_seconds is not None:
            delay = min(delay, retry_policy.max_delay_seconds)

        return delay

    @staticmethod
    def _build_result(
        request: ExecutionRequest,
        unit_name: str,
        state: ExecutionUnitState,
        result,
        error: str | None,
        attempts: int,
        started_at: datetime,
    ) -> ExecutionResult:

        completed_at = datetime.now(timezone.utc)

        return ExecutionResult(
            request_id=request.request_id,
            unit_name=unit_name,
            state=state,
            result=result,
            error=error,
            attempts=attempts,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
        )