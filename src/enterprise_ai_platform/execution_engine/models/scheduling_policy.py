"""
Scheduling policy.
"""

from __future__ import annotations

from enum import Enum


class SchedulingPolicy(str, Enum):
    """
    Queue-ordering policies from the frozen spec's Section 13.

    Fair Scheduling, Weighted Scheduling, and Custom Policies are
    deliberately not included in V1 -- FIFO/Priority/Deadline cover
    the concrete need, and the other three don't have a clear enough
    V1 use case yet to justify their added complexity.
    """

    FIFO = "fifo"

    PRIORITY = "priority"

    DEADLINE = "deadline"