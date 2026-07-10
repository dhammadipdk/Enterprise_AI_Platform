import pytest

from enterprise_ai_platform.framework.base import (
    ComponentLifecycle,
    ComponentState,
)


def test_valid_transition() -> None:
    ComponentLifecycle.validate(
        ComponentState.CREATED,
        ComponentState.INITIALIZED,
    )


def test_invalid_transition() -> None:
    with pytest.raises(ValueError):
        ComponentLifecycle.validate(
            ComponentState.CREATED,
            ComponentState.RUNNING,
        )