"""
Platform Bootstrap.

Responsible for initializing the Enterprise AI Platform.
"""

from enterprise_ai_platform.framework.core.platform_kernel import PlatformKernel


class PlatformBootstrap:
    """
    Bootstraps the Enterprise AI Platform.
    """

    def __init__(self) -> None:
        self.kernel = PlatformKernel()

    def run(self) -> None:
        """
        Execute the platform startup sequence.
        """

        self.kernel.start()