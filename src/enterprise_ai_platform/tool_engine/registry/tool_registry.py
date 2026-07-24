"""
Tool registry.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base import BaseRegistry
from enterprise_ai_platform.tool_engine.models import ToolDefinition


class ToolRegistry(BaseRegistry[ToolDefinition]):
    """
    Registry of registered tool definitions, keyed by "name@version".
    """

    pass