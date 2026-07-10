"""
Component lifecycle validation.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base.component_state import ComponentState


class ComponentLifecycle:
    """
    Validates runtime component lifecycle transitions.
    """

    _TRANSITIONS = {
        ComponentState.CREATED: {
            ComponentState.INITIALIZED,
        },
        ComponentState.INITIALIZED: {
            ComponentState.RUNNING,
        },
        ComponentState.RUNNING: {
            ComponentState.STOPPED,
        },
        ComponentState.STOPPED: {
            ComponentState.RUNNING,
            ComponentState.DISPOSED,
        },
        ComponentState.DISPOSED: set(),
        ComponentState.FAILED: set(),
    }

    @classmethod
    def can_transition(
        cls,
        current: ComponentState,
        target: ComponentState,
    ) -> bool:
        """
        Return True if a transition is allowed.
        """

        return target in cls._TRANSITIONS[current]

    @classmethod
    def validate(
        cls,
        current: ComponentState,
        target: ComponentState,
    ) -> None:
        """
        Validate a state transition.

        Raises:
            ValueError: If the transition is invalid.
        """

        if not cls.can_transition(current, target):
            raise ValueError(
                f"Invalid lifecycle transition: "
                f"{current.value} -> {target.value}"
            )