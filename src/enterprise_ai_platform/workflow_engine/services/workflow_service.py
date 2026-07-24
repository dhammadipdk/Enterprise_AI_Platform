"""
Workflow service.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)
from enterprise_ai_platform.workflow_engine.compiler import WorkflowCompiler
from enterprise_ai_platform.workflow_engine.execution import (
    ExecutionContext,
    WorkflowInstance,
    WorkflowRuntime,
)
from enterprise_ai_platform.workflow_engine.graph import WorkflowGraph
from enterprise_ai_platform.workflow_engine.loaders import (
    WorkflowDefinitionLoader,
)
from enterprise_ai_platform.workflow_engine.models import NodeType
from enterprise_ai_platform.workflow_engine.registry import WorkflowRegistry
from enterprise_ai_platform.workflow_engine.validation import (
    WorkflowValidationReport,
)


class WorkflowService(BaseService):
    """
    Public API of the Workflow Engine (frozen spec, Section 17):
    register_workflow, compile, execute, cancel, validate,
    list_workflows, get_workflow, get_execution.

    Every other subsystem interacts with workflows exclusively through
    this service, exactly as KnowledgeService and PromptService are
    the sole entry points for their engines. Nothing outside the
    Workflow Engine should reference WorkflowDefinitionLoader,
    WorkflowCompiler, WorkflowRuntime or WorkflowRegistry directly.

    resume() is deliberately not implemented: nothing in V1 can
    actually pause mid-execution yet (Human Approval and real-time
    Wait both have no handler), so there is nothing meaningful to
    resume. compare_versions()/deprecate() are also not implemented --
    unlike Prompt Engine's spec, Section 17's Public API for Workflow
    Engine doesn't list them; multi-version support via get_workflow /
    list_versions already covers "Workflow Versioning" as a
    responsibility (Section 3) without that extra lifecycle layer.
    """

    def __init__(self) -> None:

        super().__init__(name="workflow_service")

        self._loader = WorkflowDefinitionLoader()

        self._compiler = WorkflowCompiler()

        self._runtime = WorkflowRuntime()

        self._graphs = WorkflowRegistry()

        self._instances: dict[str, WorkflowInstance] = {}

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
        Dispose the service and clear all registered workflows and
        tracked executions.
        """

        self._graphs.clear()

        self._instances.clear()

        self._set_state(ComponentState.DISPOSED)

    # ------------------------------------------------------------------
    # Validation / compilation / registration
    # ------------------------------------------------------------------

    def validate_workflow(
        self,
        data: dict[str, Any],
    ) -> WorkflowValidationReport:
        """
        Load and validate raw workflow data without compiling or
        registering it.
        """

        definition = self._loader.load(data)

        return self._compiler.validate(definition)

    def compile_workflow(self, data: dict[str, Any]) -> WorkflowGraph:
        """
        Load and compile raw workflow data into a WorkflowGraph,
        without registering it.
        """

        definition = self._loader.load(data)

        return self._compiler.compile(definition)

    def register_workflow(self, data: dict[str, Any]) -> WorkflowGraph:
        """
        Load, compile, and register a workflow from raw data.
        """

        graph = self.compile_workflow(data)

        self.register_compiled_graph(graph)

        return graph

    def register_compiled_graph(self, graph: WorkflowGraph) -> None:
        """
        Register an already-compiled graph directly, bypassing loading
        and compilation.

        Overwrites any graph already registered under the same name
        and version.
        """

        key = self._key(graph.name, graph.version)

        if self._graphs.exists(key):
            self._graphs.unregister(key)

        self._graphs.register(key, graph)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_workflow(
        self,
        name: str,
        version: str | None = None,
    ) -> WorkflowGraph:
        """
        Return a registered workflow graph.

        If `version` is omitted, returns the highest registered
        version for `name`, compared numerically (e.g. "1.10.0" is
        newer than "1.9.0").
        """

        if version is not None:
            return self._graphs.get(self._key(name, version))

        versions = self.list_versions(name)

        if not versions:
            raise KeyError(f"No workflow registered with name '{name}'.")

        latest_version = max(versions, key=self._version_sort_key)

        return self._graphs.get(self._key(name, latest_version))

    def workflow_exists(
        self,
        name: str,
        version: str | None = None,
    ) -> bool:
        """
        Return True if a workflow is registered under `name` (and
        `version`, if given).
        """

        if version is not None:
            return self._graphs.exists(self._key(name, version))

        return len(self.list_versions(name)) > 0

    def list_workflows(self) -> list[str]:
        """
        Return the unique names of every registered workflow (not one
        entry per version).
        """

        names = {self._split_key(key)[0] for key in self._graphs.names()}

        return sorted(names)

    def list_versions(self, name: str) -> list[str]:
        """
        Return every registered version of `name`, oldest to newest.
        """

        versions = [
            key_version
            for key_name, key_version in (
                self._split_key(key) for key in self._graphs.names()
            )
            if key_name == name
        ]

        return sorted(versions, key=self._version_sort_key)

    # ------------------------------------------------------------------
    # Node handlers
    # ------------------------------------------------------------------

    def register_node_handler(
        self,
        node_type: NodeType,
        handler,
    ) -> None:
        """
        Register (or overwrite) the execution handler for a node type.
        """

        self._runtime.register_handler(node_type, handler)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        name: str,
        version: str | None = None,
        initial_variables: dict[str, Any] | None = None,
    ) -> WorkflowInstance:
        """
        Create and run a new execution of a registered workflow to
        completion (or failure), and return the resulting instance.
        """

        graph = self.get_workflow(name, version=version)

        instance_id = str(uuid4())

        context = ExecutionContext(initial_variables)

        instance = WorkflowInstance(instance_id, graph, context)

        self._instances[instance_id] = instance

        return self._runtime.execute(instance)

    def get_execution(self, instance_id: str) -> WorkflowInstance:
        """
        Return a tracked execution instance by id.
        """

        if instance_id not in self._instances:
            raise KeyError(
                f"No execution found with instance id '{instance_id}'."
            )

        return self._instances[instance_id]

    def cancel(self, instance_id: str) -> WorkflowInstance:
        """
        Cancel a tracked execution instance.

        A no-op if the instance has already reached a terminal state.
        """

        instance = self.get_execution(instance_id)

        return self._runtime.cancel(instance)

    def list_executions(self) -> list[str]:
        """
        Return the ids of every tracked execution instance.
        """

        return sorted(self._instances.keys())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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