"""
Tool service.
"""

from __future__ import annotations

import time
from typing import Any

from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)
from enterprise_ai_platform.tool_engine.adapters import BaseToolAdapter
from enterprise_ai_platform.tool_engine.models import (
    ToolCategory,
    ToolDefinition,
    ToolRequest,
    ToolResponse,
)
from enterprise_ai_platform.tool_engine.registry import ToolRegistry
from enterprise_ai_platform.tool_engine.validation import (
    ToolValidationIssue,
    ToolValidationReport,
)


class ToolService(BaseService):
    """
    Public API of the Tool Engine (frozen spec, Section 17).

    Implemented in this task: register_tool, validate, execute,
    disable, enable, list_tools, get_tool, health.

    Deliberately not implemented yet:
      - cancel() -- meaningful once a real asynchronous/long-running
        adapter exists; every adapter in this task is synchronous.
      - metrics() aggregation -- Section 19's metrics are aggregate
        statistics across many executions over time; there's no
        execution history yet to aggregate. ToolResponse already
        carries its own execution_time_seconds per call, which is the
        raw data a future metrics() would summarize.
      - Section 15's richer execution policies (async, batch,
        scheduled, remote) -- BaseToolAdapter.execute() is synchronous
        only for now.
      - Dependency/version/health checks beyond registration status
        (Section 13) -- these matter once real adapters with real
        external dependencies exist to check.

    Deliberately different from ModelService: adapter exceptions are
    caught here and converted into ToolResponse(status="failure", ...)
    rather than propagating raw (Section 20: "All failures generate
    structured diagnostics"). Tools span far more failure-prone
    categories (Email, Web, Calendar, ...) than model calls, and a
    workflow calling a tool needs to gracefully branch on failure via
    Decision nodes, not catch a raw exception.

    Every other subsystem interacts with tools exclusively through
    this service, exactly as KnowledgeService / PromptService /
    WorkflowService / ModelService are the sole entry points for their
    engines.
    """

    def __init__(self) -> None:

        super().__init__(name="tool_service")

        self._tools = ToolRegistry()

        self._adapters: dict[str, BaseToolAdapter] = {}

        self._disabled: set[str] = set()

    def initialize(self) -> None:
        """
        Initialize the service.
        """

        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        """
        Start the service.
        """

        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        """
        Stop the service.
        """

        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        """
        Dispose the service and clear all registered tools.
        """

        self._tools.clear()

        self._adapters.clear()

        self._disabled.clear()

        self._set_state(ComponentState.DISPOSED)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_tool(
        self,
        definition: ToolDefinition,
        adapter: BaseToolAdapter,
    ) -> None:
        """
        Register a tool definition and its adapter together.

        Overwrites any tool already registered under the same name
        and version. Re-registering does not implicitly re-enable a
        previously-disabled tool.
        """

        key = self._key(definition.name, definition.version)

        if self._tools.exists(key):
            self._tools.unregister(key)

        self._tools.register(key, definition)

        self._adapters[key] = adapter

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_tool(
        self,
        name: str,
        version: str | None = None,
    ) -> ToolDefinition:
        """
        Return a registered tool definition.

        If `version` is omitted, returns the highest registered
        version for `name`, compared numerically.
        """

        if version is not None:
            return self._tools.get(self._key(name, version))

        versions = self.list_versions(name)

        if not versions:
            raise KeyError(f"No tool registered with name '{name}'.")

        latest_version = max(versions, key=self._version_sort_key)

        return self._tools.get(self._key(name, latest_version))

    def tool_exists(
        self,
        name: str,
        version: str | None = None,
    ) -> bool:
        """
        Return True if a tool is registered under `name` (and
        `version`, if given).
        """

        if version is not None:
            return self._tools.exists(self._key(name, version))

        return len(self.list_versions(name)) > 0

    def list_tools(
        self,
        category: ToolCategory | None = None,
    ) -> list[str]:
        """
        Return the unique names of every registered tool.

        If `category` is given, only names where at least one
        registered version belongs to that category are returned.
        """

        if category is None:
            return sorted(
                {self._split_key(key)[0] for key in self._tools.names()}
            )

        matching_names: set[str] = set()

        for key in self._tools.names():

            definition = self._tools.get(key)

            if definition.category == category:
                matching_names.add(self._split_key(key)[0])

        return sorted(matching_names)

    def list_versions(self, name: str) -> list[str]:
        """
        Return every registered version of `name`, oldest to newest.
        """

        versions = [
            key_version
            for key_name, key_version in (
                self._split_key(key) for key in self._tools.names()
            )
            if key_name == name
        ]

        return sorted(versions, key=self._version_sort_key)

    # ------------------------------------------------------------------
    # Enable / disable
    # ------------------------------------------------------------------

    def disable(self, name: str, version: str | None = None) -> None:
        """
        Disable a tool. A disabled tool still exists and is still
        listed, but execute() will refuse to run it.
        """

        tool = self.get_tool(name, version=version)

        self._disabled.add(self._key(tool.name, tool.version))

    def enable(self, name: str, version: str | None = None) -> None:
        """
        Re-enable a previously-disabled tool.
        """

        tool = self.get_tool(name, version=version)

        self._disabled.discard(self._key(tool.name, tool.version))

    def is_enabled(self, name: str, version: str | None = None) -> bool:
        """
        Return True if the tool is registered and not disabled.
        """

        tool = self.get_tool(name, version=version)

        return self._key(tool.name, tool.version) not in self._disabled

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(
        self,
        name: str,
        parameters: dict[str, Any],
        version: str | None = None,
    ) -> ToolValidationReport:
        """
        Validate parameters against a tool's input_schema, without
        executing it. If the tool declares no input_schema, any
        parameters are considered valid.
        """

        tool = self.get_tool(name, version=version)

        return self._validate_parameters(tool, parameters)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        name: str,
        parameters: dict[str, Any] | None = None,
        version: str | None = None,
        granted_permissions: set[str] | None = None,
        execution_context: dict[str, Any] | None = None,
        timeout_seconds: float | None = None,
    ) -> ToolResponse:
        """
        Execute a registered, enabled tool.

        Permission checks and parameter validation happen before the
        adapter is ever called, and raise immediately on failure --
        these represent an authoring/authorization mistake, not tool
        runtime behavior. Once execution actually starts, any failure
        (including an unexpected adapter exception) is captured as a
        ToolResponse(status="failure", ...) instead of raised.

        Raises:
            KeyError: no such tool registered.
            RuntimeError: the tool is disabled.
            PermissionError: required permissions are missing.
            ValueError: parameters don't match the tool's input_schema.
        """

        tool = self.get_tool(name, version=version)

        key = self._key(tool.name, tool.version)

        if key in self._disabled:
            raise RuntimeError(
                f"Tool '{name}' (version {tool.version}) is disabled."
            )

        parameters = parameters or {}

        self._check_permissions(tool, granted_permissions or set())

        report = self._validate_parameters(tool, parameters)

        if not report.is_valid:
            error_messages = "; ".join(
                issue.message for issue in report.errors
            )
            raise ValueError(
                f"Invalid parameters for tool '{name}': {error_messages}"
            )

        request = ToolRequest(
            tool_name=tool.name,
            parameters=parameters,
            execution_context=execution_context,
            timeout_seconds=timeout_seconds,
        )

        adapter = self._adapters[key]

        start = time.monotonic()

        try:
            raw_response = adapter.execute(request, tool)
        except Exception as error:
            elapsed = time.monotonic() - start
            return ToolResponse(
                request_id=request.request_id,
                status="failure",
                error=str(error),
                execution_time_seconds=elapsed,
            )

        elapsed = time.monotonic() - start

        return ToolResponse(
            request_id=raw_response.request_id,
            response_id=raw_response.response_id,
            status=raw_response.status,
            result=raw_response.result,
            error=raw_response.error,
            artifacts=raw_response.artifacts,
            execution_time_seconds=elapsed,
            metadata=raw_response.metadata,
        )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self, name: str, version: str | None = None) -> bool:
        """
        Return True if the tool is registered and enabled.

        For now this only confirms registration/enablement status;
        deeper health checks (e.g. pinging a real external dependency)
        are meaningful once a real adapter exists to check.
        """

        if not self.tool_exists(name, version=version):
            return False

        return self.is_enabled(name, version=version)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_permissions(
        tool: ToolDefinition,
        granted_permissions: set[str],
    ) -> None:

        required = {permission.name for permission in tool.permissions}

        missing = sorted(required - granted_permissions)

        if missing:
            raise PermissionError(
                f"Cannot execute tool '{tool.name}': missing required "
                f"permissions: {missing}."
            )

    @staticmethod
    def _validate_parameters(
        tool: ToolDefinition,
        parameters: dict[str, Any],
    ) -> ToolValidationReport:

        if tool.input_schema is None:
            return ToolValidationReport(issues=[])

        import jsonschema

        validator = jsonschema.Draft7Validator(tool.input_schema)

        issues = [
            ToolValidationIssue(
                severity="error",
                code="INVALID_PARAMETER",
                message=error.message,
            )
            for error in validator.iter_errors(parameters)
        ]

        return ToolValidationReport(issues=issues)

    @staticmethod
    def _key(name: str, version: str) -> str:

        return f"{name}@{version}"

    @staticmethod
    def _split_key(key: str) -> tuple[str, str]:

        name, _, version = key.rpartition("@")

        return name, version

    @staticmethod
    def _version_sort_key(version: str) -> tuple[int, ...]:

        return tuple(int(part) for part in version.split("."))