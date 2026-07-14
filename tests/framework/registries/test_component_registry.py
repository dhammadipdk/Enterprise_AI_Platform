from enterprise_ai_platform.framework.base import BaseComponent, ComponentState
from enterprise_ai_platform.framework.registries import ComponentRegistry


class DummyComponent(BaseComponent):

    def initialize(self) -> None:
        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        self._set_state(ComponentState.DISPOSED)


def test_component_registry() -> None:

    registry = ComponentRegistry()

    component = DummyComponent("Component")

    registry.register("component", component)

    assert registry.exists("component")

    assert registry.get("component") is component

    assert registry.names() == ["component"]