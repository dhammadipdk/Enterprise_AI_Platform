"""
Configuration Service.
"""

from enterprise_ai_platform.configuration.settings import Settings
from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)


class ConfigurationService(BaseService):
    """
    Provides platform configuration.
    """

    def __init__(self) -> None:
        super().__init__("ConfigurationService")

        self._settings = Settings()

    @property
    def settings(self) -> Settings:
        return self._settings

    def initialize(self) -> None:
        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        self._set_state(ComponentState.DISPOSED)