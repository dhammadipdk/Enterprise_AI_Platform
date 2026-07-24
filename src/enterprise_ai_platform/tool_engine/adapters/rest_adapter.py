"""
REST tool adapter.
"""

from __future__ import annotations

from enterprise_ai_platform.tool_engine.adapters.base_tool_adapter import (
    BaseToolAdapter,
)
from enterprise_ai_platform.tool_engine.models import (
    ToolDefinition,
    ToolRequest,
    ToolResponse,
)

_BODY_METHODS = {"POST", "PUT", "PATCH"}


class RESTAdapter(BaseToolAdapter):
    """
    Wraps a REST API endpoint as a tool.

    Endpoint details come from ToolDefinition.configuration -- "url"
    (required), "method" (default "GET"), "headers" (default {}) --
    so ONE RESTAdapter instance serves any number of DIFFERENT REST
    tools; each tool registration supplies its own configuration, the
    same "generic adapter class, tool-specific configuration" pattern
    used by OllamaAdapter/AnthropicAdapter/OpenAIAdapter for reading
    model-name overrides from ModelDefinition.configuration.

    ToolRequest.parameters becomes the JSON body for POST/PUT/PATCH,
    or query string parameters for GET/DELETE -- the most common REST
    tool-calling convention.
    """

    def __init__(self, default_timeout_seconds: float = 30.0) -> None:

        self._default_timeout_seconds = default_timeout_seconds

    def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
    ) -> ToolResponse:
        """
        Send an HTTP request built from the tool's configuration and
        the request's parameters.
        """

        import requests

        url = tool.configuration.get("url")

        if not url:
            raise ValueError(
                f"Tool '{tool.name}' has no 'url' in its configuration; "
                f"RESTAdapter requires one."
            )

        method = tool.configuration.get("method", "GET").upper()

        headers = tool.configuration.get("headers", {})

        timeout = request.timeout_seconds or self._default_timeout_seconds

        if method in _BODY_METHODS:
            http_response = requests.request(
                method,
                url,
                json=request.parameters,
                headers=headers,
                timeout=timeout,
            )
        else:
            http_response = requests.request(
                method,
                url,
                params=request.parameters,
                headers=headers,
                timeout=timeout,
            )

        http_response.raise_for_status()

        try:
            result = http_response.json()
        except ValueError:
            result = http_response.text

        return ToolResponse(
            request_id=request.request_id,
            status="success",
            result=result,
            metadata={"status_code": http_response.status_code},
        )