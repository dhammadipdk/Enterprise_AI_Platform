import pytest

from enterprise_ai_platform.execution_engine import (
    ExecutionDefinition,
    ExecutionRetryPolicy,
    RetryStrategy,
)


def test_defaults() -> None:

    definition = ExecutionDefinition(name="calculate_premium")

    assert definition.timeout_seconds is None

    assert definition.retry_policy.strategy == RetryStrategy.NONE

    assert definition.retry_policy.max_attempts == 1

    assert definition.priority == 0


def test_is_frozen() -> None:

    definition = ExecutionDefinition(name="calculate_premium")

    with pytest.raises(Exception):
        definition.name = "changed"


def test_retry_policy_is_frozen() -> None:

    policy = ExecutionRetryPolicy(strategy=RetryStrategy.FIXED, max_attempts=3)

    with pytest.raises(Exception):
        policy.max_attempts = 5