"""
Context category.
"""

from __future__ import annotations

from enum import Enum


class ContextCategory(str, Enum):
    """
    The seven named context buckets from the frozen spec's Section 8
    PlatformContext (called "ExecutionContext" in the spec; renamed
    here -- see PlatformContext's docstring for why).
    """

    WORKFLOW = "workflow"

    KNOWLEDGE = "knowledge"

    MEMORY = "memory"

    USER = "user"

    EXECUTION = "execution"

    TOOL = "tool"

    MODEL = "model"