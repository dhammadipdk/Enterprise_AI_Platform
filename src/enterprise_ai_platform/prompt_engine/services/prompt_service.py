"""
Prompt service.
"""

from __future__ import annotations

from typing import Any, Callable

from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)
from enterprise_ai_platform.prompt_engine.compiler import PromptCompiler
from enterprise_ai_platform.prompt_engine.loaders import (
    PromptDefinitionLoader,
)
from enterprise_ai_platform.prompt_engine.models import (
    PromptInstance,
    PromptTemplate,
)
from enterprise_ai_platform.prompt_engine.registry import PromptRegistry
from enterprise_ai_platform.prompt_engine.renderer import PromptRenderer
from enterprise_ai_platform.prompt_engine.resolution import (
    VariableResolutionResult,
    VariableResolver,
)
from enterprise_ai_platform.prompt_engine.validation import (
    PromptValidationReport,
)

ListAssetsFunction = Callable[[str, str], list[str]]
LoadAssetContentFunction = Callable[[str, str, str], Any]


class PromptService(BaseService):
    """
    Public API of the Prompt Engine.

    Every other subsystem interacts with prompts exclusively through
    this service, exactly as KnowledgeService is the sole entry point
    for the Knowledge Engine. Nothing outside the Prompt Engine should
    reference PromptDefinitionLoader, PromptCompiler, VariableResolver,
    PromptRenderer or PromptRegistry directly.

    Deliberately does not import KnowledgeService: the frozen spec
    (Section 23) says prompts are stored inside the Knowledge
    Repository, but no engine in this codebase imports another
    engine's concrete classes. load_from_knowledge() takes injected
    callables matching KnowledgeService.list_assets /
    load_asset_content's exact signatures instead -- the same
    dependency-injection approach used throughout (Retriever,
    HybridRetriever, GraphBuilder), keeping this engine self-contained
    while still making the integration real and testable.
    """

    def __init__(self) -> None:

        super().__init__(name="prompt_service")

        self._loader = PromptDefinitionLoader()

        self._compiler = PromptCompiler()

        self._resolver = VariableResolver()

        self._renderer = PromptRenderer()

        self._registry = PromptRegistry()

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
        Dispose the service and clear all registered prompts.
        """

        self._registry.clear()

        self._set_state(ComponentState.DISPOSED)

    # ------------------------------------------------------------------
    # Validation / compilation / registration
    # ------------------------------------------------------------------

    def validate_prompt(self, data: dict[str, Any]) -> PromptValidationReport:
        """
        Load and validate raw prompt data without compiling or
        registering it.
        """

        definition = self._loader.load(data)

        return self._compiler.validate(definition)

    def compile_prompt(self, data: dict[str, Any]) -> PromptTemplate:
        """
        Load and compile raw prompt data into a PromptTemplate,
        without registering it.
        """

        definition = self._loader.load(data)

        return self._compiler.compile(definition)

    def register_prompt(self, data: dict[str, Any]) -> PromptTemplate:
        """
        Load, compile, and register a prompt from raw data (typically
        a dict parsed from a YAML prompt asset).
        """

        template = self.compile_prompt(data)

        self.register_compiled_template(template)

        return template

    def register_compiled_template(self, template: PromptTemplate) -> None:
        """
        Register an already-compiled template directly, bypassing
        loading and compilation.

        Overwrites any template already registered under the same
        name and version.
        """

        key = self._key(template.name, template.version)

        if self._registry.exists(key):
            self._registry.unregister(key)

        self._registry.register(key, template)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_prompt(
        self,
        name: str,
        version: str | None = None,
    ) -> PromptTemplate:
        """
        Return a registered prompt template.

        If `version` is omitted, returns the highest registered
        version for `name` (compared numerically, e.g. "1.10.0" is
        newer than "1.9.0" -- not by plain string comparison).
        """

        if version is not None:
            return self._registry.get(self._key(name, version))

        versions = self.list_versions(name)

        if not versions:
            raise KeyError(f"No prompt registered with name '{name}'.")

        latest_version = max(versions, key=self._version_sort_key)

        return self._registry.get(self._key(name, latest_version))

    def prompt_exists(
        self,
        name: str,
        version: str | None = None,
    ) -> bool:
        """
        Return True if a prompt is registered under `name` (and
        `version`, if given).
        """

        if version is not None:
            return self._registry.exists(self._key(name, version))

        return len(self.list_versions(name)) > 0

    def list_prompts(self) -> list[str]:
        """
        Return the unique names of every registered prompt (not one
        entry per version).
        """

        names = {
            self._split_key(key)[0] for key in self._registry.names()
        }

        return sorted(names)

    def list_versions(self, name: str) -> list[str]:
        """
        Return every registered version of `name`, oldest to newest.
        """

        versions = [
            key_version
            for key_name, key_version in (
                self._split_key(key) for key in self._registry.names()
            )
            if key_name == name
        ]

        return sorted(versions, key=self._version_sort_key)

    # ------------------------------------------------------------------
    # Resolution / rendering
    # ------------------------------------------------------------------

    def resolve_variables(
        self,
        name: str,
        provided_values: dict[str, Any],
        version: str | None = None,
    ) -> VariableResolutionResult:
        """
        Resolve a registered prompt's variables against provided
        values, without rendering.
        """

        template = self.get_prompt(name, version=version)

        return self._resolver.resolve(template, provided_values)

    def render_prompt(
        self,
        name: str,
        provided_values: dict[str, Any],
        version: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> PromptInstance:
        """
        Resolve and render a registered prompt in one call.

        Raises ValueError if variable resolution has any error-level
        issue (see VariableResolver / PromptRenderer).
        """

        template = self.get_prompt(name, version=version)

        resolution = self._resolver.resolve(template, provided_values)

        return self._renderer.render(template, resolution, context=context)

    # ------------------------------------------------------------------
    # Knowledge Repository integration
    # ------------------------------------------------------------------

    def load_from_knowledge(
        self,
        list_assets_fn: ListAssetsFunction,
        load_asset_content_fn: LoadAssetContentFunction,
        repository: str,
        domain: str = "prompts",
    ) -> list[PromptTemplate]:
        """
        Load, compile, and register every prompt asset found in a
        Knowledge Repository domain (by default, "prompts", matching
        knowledge/platform/prompts/ per the frozen spec's Section 23).

        `list_assets_fn` / `load_asset_content_fn` are expected to
        match KnowledgeService.list_assets(repository, domain) and
        KnowledgeService.load_asset_content(repository, domain, asset)
        respectively.
        """

        templates: list[PromptTemplate] = []

        for asset_name in list_assets_fn(repository, domain):

            raw_data = load_asset_content_fn(repository, domain, asset_name)

            templates.append(self.register_prompt(raw_data))

        return templates

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