"""
Configuration Service.
"""

from enterprise_ai_platform.configuration.settings import Settings


class ConfigurationService:
    """
    Provides platform configuration.
    """

    def __init__(self) -> None:
        self._settings = Settings()

    @property
    def settings(self) -> Settings:
        return self._settings