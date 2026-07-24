"""
Model service.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)
from enterprise_ai_platform.model_engine.adapters import BaseModelAdapter
from enterprise_ai_platform.model_engine.models import (
    ModelCapability,
    ModelDefinition,
    ModelRequest,
    ModelResponse,
    ProviderDefinition,
)
from enterprise_ai_platform.model_engine.registry import ModelRegistry
from enterprise_ai_platform.model_engine.structured_output import (
    StructuredOutputEnforcer,
)


class ModelService(BaseService):
    """
    Public API of the Model Engine (frozen spec, Section 15).

    Implemented so far: register_provider, register_model,
    list_models, get_model, execute (including structured output),
    health.

    Deliberately not implemented yet:
      - stream() -- Section 17 streaming is its own later task; this
        task's execute() is synchronous, non-streaming only.
      - metrics() aggregation -- Section 20's metrics (success rate,
        throughput, etc.) are aggregate statistics computed across
        many requests over time; there's no usage history to
        aggregate yet. Each ModelResponse already carries its own
        latency_seconds/token_usage/cost, which is the raw data a
        future metrics() would summarize.
      - Capability/cost/latency-based routing (Section 13, 19) --
        execute() requires an explicit model name for now; a
        ModelRouter making policy-based selections (cheapest, fastest,
        ...) is a sensible later addition once real usage data exists
        to route on.
      - Provider-native structured output modes (OpenAI response_
        format, Anthropic tool-forcing, Ollama's format parameter) --
        structured output is enforced uniformly at this layer instead
        (see StructuredOutputEnforcer's docstring), so it works
        identically no matter which provider is active. Native modes
        remain a reasonable future optimization on top of this.

    Every other subsystem interacts with models exclusively through
    this service, exactly as KnowledgeService / PromptService /
    WorkflowService are the sole entry points for their engines.
    """

    def __init__(self) -> None:

        super().__init__(name="model_service")

        self._providers: dict[str, BaseModelAdapter] = {}

        self._provider_definitions: dict[str, ProviderDefinition] = {}

        self._models = ModelRegistry()

        self._structured_output = StructuredOutputEnforcer()

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
        Dispose the service and clear all registered providers and
        models.
        """

        self._models.clear()

        self._providers.clear()

        self._provider_definitions.clear()

        self._set_state(ComponentState.DISPOSED)

    # ------------------------------------------------------------------
    # Provider registration
    # ------------------------------------------------------------------

    def register_provider(
        self,
        definition: ProviderDefinition,
        adapter: BaseModelAdapter,
    ) -> None:
        """
        Register a provider adapter under `definition.name`.

        Overwrites any provider already registered under the same
        name.
        """

        self._provider_definitions[definition.name] = definition

        self._providers[definition.name] = adapter

    def provider_exists(self, name: str) -> bool:
        """
        Return True if a provider is registered under `name`.
        """

        return name in self._providers

    def list_providers(self) -> list[str]:
        """
        Return the names of every registered provider.
        """

        return sorted(self._providers.keys())

    def get_provider_definition(self, name: str) -> ProviderDefinition:
        """
        Return a registered provider's definition.
        """

        if name not in self._provider_definitions:
            raise KeyError(f"No provider registered with name '{name}'.")

        return self._provider_definitions[name]

    # ------------------------------------------------------------------
    # Model registration
    # ------------------------------------------------------------------

    def register_model(self, definition: ModelDefinition) -> None:
        """
        Register a model definition.

        Raises ValueError if the model's declared provider hasn't been
        registered yet -- a model can't be invoked without one.
        """

        if not self.provider_exists(definition.provider):
            raise ValueError(
                f"Cannot register model '{definition.name}': no "
                f"provider registered with name '{definition.provider}'. "
                f"Register the provider first."
            )

        key = self._key(definition.name, definition.version)

        if self._models.exists(key):
            self._models.unregister(key)

        self._models.register(key, definition)

    def get_model(
        self,
        name: str,
        version: str | None = None,
    ) -> ModelDefinition:
        """
        Return a registered model definition.

        If `version` is omitted, returns the highest registered
        version for `name`, compared numerically.
        """

        if version is not None:
            return self._models.get(self._key(name, version))

        versions = self.list_versions(name)

        if not versions:
            raise KeyError(f"No model registered with name '{name}'.")

        latest_version = max(versions, key=self._version_sort_key)

        return self._models.get(self._key(name, latest_version))

    def model_exists(
        self,
        name: str,
        version: str | None = None,
    ) -> bool:
        """
        Return True if a model is registered under `name` (and
        `version`, if given).
        """

        if version is not None:
            return self._models.exists(self._key(name, version))

        return len(self.list_versions(name)) > 0

    def list_models(
        self,
        capability: ModelCapability | None = None,
    ) -> list[str]:
        """
        Return the unique names of every registered model.

        If `capability` is given, only names where at least one
        registered version declares that capability are returned.
        """

        if capability is None:
            return sorted(
                {self._split_key(key)[0] for key in self._models.names()}
            )

        matching_names: set[str] = set()

        for key in self._models.names():

            definition = self._models.get(key)

            if capability in definition.capabilities:
                matching_names.add(self._split_key(key)[0])

        return sorted(matching_names)

    def list_versions(self, name: str) -> list[str]:
        """
        Return every registered version of `name`, oldest to newest.
        """

        versions = [
            key_version
            for key_name, key_version in (
                self._split_key(key) for key in self._models.names()
            )
            if key_name == name
        ]

        return sorted(versions, key=self._version_sort_key)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        model_name: str,
        prompt: str,
        version: str | None = None,
        system_prompt: str | None = None,
        parameters: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        response_schema: Any = None,
    ) -> ModelResponse:
        """
        Execute a prompt against a registered model and return its
        response.

        If `response_schema` is given (a JSON schema dict, or a
        pydantic BaseModel subclass), the prompt is augmented with
        explicit formatting instructions, the raw model output is
        parsed as JSON and validated against the schema, and the
        result is populated on ModelResponse.structured_output. Raises
        ValueError if the output can't be parsed as JSON or doesn't
        match the schema.
        """

        model = self.get_model(model_name, version=version)

        adapter = self._providers[model.provider]

        schema_dict = self._resolve_schema(response_schema)

        final_prompt = prompt

        if schema_dict is not None:
            final_prompt = self._structured_output.augment_prompt(
                prompt,
                schema_dict,
            )

        request = ModelRequest(
            prompt=final_prompt,
            system_prompt=system_prompt,
            parameters=parameters or {},
            context=context,
            response_schema=schema_dict,
        )

        raw_response = adapter.invoke(request, model)

        if schema_dict is None:
            return raw_response

        structured = self._structured_output.parse_response(
            raw_response.text,
            schema_dict,
        )

        return ModelResponse(
            request_id=raw_response.request_id,
            response_id=raw_response.response_id,
            text=raw_response.text,
            structured_output=structured,
            tool_calls=raw_response.tool_calls,
            token_usage=raw_response.token_usage,
            cost=raw_response.cost,
            latency_seconds=raw_response.latency_seconds,
            metadata=raw_response.metadata,
        )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self, provider_name: str) -> bool:
        """
        Return True if a provider is registered and considered
        available.

        For now this only confirms registration; real health checks
        (e.g. pinging the provider's API) are meaningful once a real
        adapter exists to check.
        """

        return self.provider_exists(provider_name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_schema(response_schema: Any) -> dict[str, Any] | None:

        if response_schema is None:
            return None

        if isinstance(response_schema, dict):
            return response_schema

        # A pydantic BaseModel subclass -- generate its JSON schema.
        # Duck-typed rather than isinstance-checked against
        # pydantic.BaseModel to avoid a hard import of pydantic here
        # beyond what the rest of this module already needs.
        if isinstance(response_schema, type) and hasattr(
            response_schema, "model_json_schema"
        ):
            return response_schema.model_json_schema()

        raise TypeError(
            "response_schema must be a JSON schema dict or a pydantic "
            "BaseModel subclass."
        )

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