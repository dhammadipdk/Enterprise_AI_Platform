"""
Platform registries.
"""

from enterprise_ai_platform.framework.registries.component_registry import (
    ComponentRegistry,
)
from enterprise_ai_platform.framework.registries.service_registry import (
    ServiceRegistry,
)

__all__ = [
    "ComponentRegistry",
    "ServiceRegistry",
]