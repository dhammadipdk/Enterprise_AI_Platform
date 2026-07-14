"""
Service registry.
"""

from enterprise_ai_platform.framework.base import (
    BaseRegistry,
    BaseService,
)


class ServiceRegistry(BaseRegistry[BaseService]):
    """
    Registry for platform services.
    """

    pass