"""
Python function tool adapter.
"""

from __future__ import annotations

from typing import Any, Callable

from enterprise_ai_platform.tool_engine.adapters.base_tool_adapter import (
    BaseToolAdapter,
)
from enterprise_ai_platform.tool_engine.models import (
    ToolDefinition,
    ToolRequest,
    ToolResponse,
)


class PythonFunctionAdapter(BaseToolAdapter):
    """
    Wraps an arbitrary Python callable as a tool.

    No external dependencies or credentials needed -- the most
    immediately usable adapter, e.g. for wrapping a real premium-
    calculation function or any other business rule that already
    exists as in-process Python logic.

    The wrapped function receives ToolRequest.parameters as keyword
    arguments, and its return value becomes the response's `result`.
    Exceptions are deliberately NOT caught here -- ToolService already
    catches any exception from adapter.execute() and converts it into
    a ToolResponse(status="failure", ...); catching it again here
    would be redundant with that established layering.
    """

    def __init__(self, func: Callable[..., Any]) -> None:

        self._func = func

    def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
    ) -> ToolResponse:
        """
        Call the wrapped function with the request's parameters as
        keyword arguments.
        """

        result = self._func(**request.parameters)

        return ToolResponse(
            request_id=request.request_id,
            status="success",
            result=result,
        )