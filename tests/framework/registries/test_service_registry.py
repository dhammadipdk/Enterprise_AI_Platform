from enterprise_ai_platform.framework.base import BaseService, ComponentState
from enterprise_ai_platform.framework.registries import ServiceRegistry


class DummyService(BaseService):

    def initialize(self) -> None:
        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        self._set_state(ComponentState.DISPOSED)


def test_service_registry() -> None:

    registry = ServiceRegistry()

    service = DummyService("Service")

    registry.register("service", service)

    assert registry.exists("service")

    assert registry.get("service") is service

    assert registry.names() == ["service"]