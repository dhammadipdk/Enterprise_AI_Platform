"""
Platform settings.
"""

from pydantic import BaseModel


class Settings(BaseModel):
    """
    Runtime platform settings.
    """

    environment: str = "development"

    log_level: str = "INFO"

    platform_name: str = "Enterprise AI Platform"

    version: str = "1.0.0"