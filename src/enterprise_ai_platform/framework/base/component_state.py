"""
Component lifecycle states.
"""

from enum import Enum


class ComponentState(str, Enum):
    """
    Represents the lifecycle state of a runtime component.
    """

    CREATED = "CREATED"

    INITIALIZED = "INITIALIZED"

    RUNNING = "RUNNING"

    STOPPED = "STOPPED"

    DISPOSED = "DISPOSED"

    FAILED = "FAILED"