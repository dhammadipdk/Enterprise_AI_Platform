"""
Platform Kernel.

Coordinates the Enterprise AI Platform runtime.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base import (
    BaseComponent,
    BaseService,
)
from enterprise_ai_platform.framework.registries import (
    ComponentRegistry,
    ServiceRegistry,
)


class PlatformKernel:
    """
    Central runtime coordinator.
    """

    def __init__(self) -> None:

        self._components = ComponentRegistry()

        self._services = ServiceRegistry()

    @property
    def component_registry(self) -> ComponentRegistry:
        """
        Return the component registry.
        """

        return self._components

    @property
    def service_registry(self) -> ServiceRegistry:
        """
        Return the service registry.
        """

        return self._services

    def register_component(
        self,
        name: str,
        component: BaseComponent,
    ) -> None:
        """
        Register a runtime component.
        """

        self._components.register(
            name,
            component,
        )

    def register_service(
        self,
        name: str,
        service: BaseService,
    ) -> None:
        """
        Register a runtime service.
        """

        self._services.register(
            name,
            service,
        )

        self._components.register(
            name,
            service,
        )

    def initialize(self) -> None:
        """
        Initialize all registered components.
        """

        for name in self._components.names():
            self._components.get(name).initialize()

    def start(self) -> None:
        """
        Start all registered components.
        """

        for name in self._components.names():
            self._components.get(name).start()

    def stop(self) -> None:
        """
        Stop all registered components.
        """

        for name in self._components.names():
            self._components.get(name).stop()

    def dispose(self) -> None:
        """
        Dispose all registered components.
        """

        for name in self._components.names():
            self._components.get(name).dispose()