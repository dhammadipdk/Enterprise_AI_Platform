from enterprise_ai_platform.framework.base import ComponentState


def test_component_state_values() -> None:
    assert ComponentState.CREATED.value == "CREATED"
    assert ComponentState.RUNNING.value == "RUNNING"