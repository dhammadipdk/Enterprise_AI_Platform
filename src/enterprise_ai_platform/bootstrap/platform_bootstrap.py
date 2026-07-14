"""
Platform Bootstrap.
"""

from loguru import logger

from enterprise_ai_platform.configuration import ConfigurationService
from enterprise_ai_platform.framework.core import PlatformKernel
from enterprise_ai_platform.logging import LoggingService


class PlatformBootstrap:
    """
    Bootstraps the Enterprise AI Platform.
    """

    def __init__(self) -> None:

        self.kernel = PlatformKernel()

        self.configuration = ConfigurationService()

        self.logging = LoggingService()

    def run(self) -> None:

        self.kernel.register_service(
            "configuration",
            self.configuration,
        )

        self.kernel.register_service(
            "logging",
            self.logging,
        )

        self.kernel.initialize()

        self.kernel.start()

        settings = self.configuration.settings

        logger.info(
            f"Starting {settings.platform_name} "
            f"{settings.version} "
            f"({settings.environment})"
        )