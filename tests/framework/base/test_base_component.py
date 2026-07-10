from enterprise_ai_platform.framework.base import BaseService
from enterprise_ai_platform.framework.base import ComponentState
from uuid import UUID


class DummyService(BaseService):

    def initialize(self) -> None:
        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        self._set_state(ComponentState.DISPOSED)


def test_component_lifecycle() -> None:

    service = DummyService("Dummy")

    assert isinstance(service.id, UUID)
    assert service.name == "Dummy"
    assert service.state == ComponentState.CREATED

    service.initialize()

    assert service.state == ComponentState.INITIALIZED

    service.start()

    assert service.is_running

    service.stop()

    assert service.state == ComponentState.STOPPED

    service.dispose()

    assert service.state == ComponentState.DISPOSED