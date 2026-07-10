"""
Platform Bootstrap.
"""

from enterprise_ai_platform.configuration import ConfigurationService
from enterprise_ai_platform.logging import LoggingService


class PlatformBootstrap:
    """
    Bootstraps the platform.
    """

    def __init__(self) -> None:

        self.configuration = ConfigurationService()

        self.logging = LoggingService()

    def run(self) -> None:

        self.logging.initialize()

        settings = self.configuration.settings

        from loguru import logger

        logger.info(
            f"Starting {settings.platform_name} "
            f"{settings.version} "
            f"({settings.environment})"
        )