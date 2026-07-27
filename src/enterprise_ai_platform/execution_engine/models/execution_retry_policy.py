"""
Execution retry policy.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.execution_engine.models.retry_strategy import (
    RetryStrategy,
)


class ExecutionRetryPolicy(BaseModel):
    """
    Retry configuration for one ExecutionDefinition (Section 14).

    Named ExecutionRetryPolicy, not RetryPolicy, to avoid colliding
    with workflow_engine.models.RetryPolicy -- a simpler model
    (max_attempts + backoff_seconds only) built for a different,
    narrower purpose (per-node retry hints inside a workflow
    definition). This one models a genuine retry strategy (fixed /
    linear / exponential backoff, with an optional cap), appropriate
    for the more general Execution Engine.
    """

    model_config = ConfigDict(frozen=True)

    strategy: RetryStrategy = RetryStrategy.NONE

    max_attempts: int = 1

    base_delay_seconds: float = 0.0

    max_delay_seconds: float | None = None