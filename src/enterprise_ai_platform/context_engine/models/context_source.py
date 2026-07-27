"""
Context source.
"""

from __future__ import annotations

from enum import Enum


class ContextSource(str, Enum):
    """
    Every source the frozen spec (Section 9) names -- which subsystem
    a ContextFragment originated from.
    """

    KNOWLEDGE = "knowledge"

    MEMORY = "memory"

    WORKFLOW = "workflow"

    PROMPT = "prompt"

    EXECUTION = "execution"

    USER_SESSION = "user_session"

    EXTERNAL_SYSTEM = "external_system"

    CUSTOM = "custom"