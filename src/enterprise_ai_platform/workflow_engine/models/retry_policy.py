"""
Retry policy.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RetryPolicy(BaseModel):
    """
    Retry behavior for a single workflow node.
    """

    model_config = ConfigDict(frozen=True)

    max_attempts: int = 1

    backoff_seconds: float = 0.0