"""
Logging Service.
"""

from loguru import logger


class LoggingService:
    """
    Configures platform logging.
    """

    def initialize(self) -> None:
        """
        Initialize logging.
        """

        logger.remove()

        logger.add(
            sink=lambda message: print(message, end=""),
            level="INFO",
            colorize=True,
        )

        logger.info("Logging initialized.")