from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)
from enterprise_ai_platform.framework.core import PlatformKernel


class DummyService(BaseService):

    def initialize(self) -> None:
        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        self._set_state(ComponentState.DISPOSED)


def test_platform_kernel_lifecycle() -> None:

    kernel = PlatformKernel()

    service = DummyService("Logging")

    kernel.register_service(
        "logging",
        service,
    )

    kernel.initialize()

    assert service.state == ComponentState.INITIALIZED

    kernel.start()

    assert service.state == ComponentState.RUNNING

    kernel.stop()

    assert service.state == ComponentState.STOPPED

    kernel.dispose()

    assert service.state == ComponentState.DISPOSED