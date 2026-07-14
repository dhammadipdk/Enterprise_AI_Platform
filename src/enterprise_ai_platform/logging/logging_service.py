"""
Logging Service.
"""

from loguru import logger

from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)


class LoggingService(BaseService):
    """
    Configures platform logging.
    """

    def __init__(self) -> None:
        super().__init__("LoggingService")

    def initialize(self) -> None:

        logger.remove()

        logger.add(
            sink=lambda message: print(message, end=""),
            level="INFO",
            colorize=True,
        )

        logger.info("Logging initialized.")

        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        self._set_state(ComponentState.DISPOSED)