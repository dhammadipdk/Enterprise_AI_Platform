"""
Base tool adapter contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from enterprise_ai_platform.tool_engine.models import (
    ToolDefinition,
    ToolRequest,
    ToolResponse,
)


class BaseToolAdapter(ABC):
    """
    Base class for all tool adapters (Section 16).

    Unlike Model Engine's providers (one shared client serving many
    models), each tool gets its own adapter instance at registration
    time -- a REST tool wrapping one specific endpoint, or a Python
    tool wrapping one specific function, is inherently tool-specific
    configuration, not a shared resource multiple tools reuse.

    Only synchronous execution is defined here for now; the richer
    Section 15 execution policies (async, batch, scheduled, remote)
    are a later concern once there's a genuine need driving them.
    """

    @abstractmethod
    def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
    ) -> ToolResponse:
        """
        Execute the tool and return its response.
        """