"""
Component registry.
"""

from enterprise_ai_platform.framework.base import (
    BaseComponent,
    BaseRegistry,
)


class ComponentRegistry(BaseRegistry[BaseComponent]):
    """
    Registry for runtime components.
    """

    pass