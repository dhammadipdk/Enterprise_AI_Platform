"""
Base runtime component.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from enterprise_ai_platform.framework.base.component_state import ComponentState
from enterprise_ai_platform.framework.base.component_lifecycle import (
    ComponentLifecycle,
)

class BaseComponent(ABC):
    """
    Base class for all runtime components.

    Components participate in the platform lifecycle.
    """

    def __init__(self, name: str) -> None:
        self._id: UUID = uuid4()
        self._name = name
        self._state = ComponentState.CREATED

    @property
    def name(self) -> str:
        """Return the component name."""

        return self._name

    @property
    def id(self) -> UUID:
        """
        Return the component identifier.
        """

        return self._id

    @property
    def state(self) -> ComponentState:
        """Return the current lifecycle state."""

        return self._state

    @property
    def is_running(self) -> bool:
        """Return True if the component is running."""

        return self._state == ComponentState.RUNNING

    def _set_state(self, state: ComponentState) -> None:
        """
        Update the lifecycle state after validation.
        """

        ComponentLifecycle.validate(self._state, state)

        self._state = state

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the component.
        """

    @abstractmethod
    def start(self) -> None:
        """
        Start the component.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the component.
        """

    @abstractmethod
    def dispose(self) -> None:
        """
        Dispose of the component.
        """