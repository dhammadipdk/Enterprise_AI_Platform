"""
Retry strategy.
"""

from __future__ import annotations

from enum import Enum


class RetryStrategy(str, Enum):
    """
    Retry strategies from the frozen spec's Section 14.
    """

    NONE = "none"

    FIXED = "fixed"

    EXPONENTIAL_BACKOFF = "exponential_backoff"

    LINEAR_BACKOFF = "linear_backoff"