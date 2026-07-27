"""
Context service.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.context_engine.builder import ContextBuilder
from enterprise_ai_platform.context_engine.models import (
    ContextCategory,
    ContextFragment,
    ContextSource,
    PlatformContext,
)
from enterprise_ai_platform.context_engine.validation import (
    ContextValidationReport,
)
from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)

_CATEGORY_FIELD_NAMES: dict[ContextCategory, str] = {
    ContextCategory.WORKFLOW: "workflow_context",
    ContextCategory.KNOWLEDGE: "knowledge_context",
    ContextCategory.MEMORY: "memory_context",
    ContextCategory.USER: "user_context",
    ContextCategory.EXECUTION: "execution_context",
    ContextCategory.TOOL: "tool_context",
    ContextCategory.MODEL: "model_context",
}


class ContextService(BaseService):
    """
    Public API of the Context Engine (frozen spec, Section 15).

    Implemented in this task: build, merge, validate, serialize,
    deserialize, list_sources, statistics.

    Deliberately not implemented yet:
      - Token-aware / semantic compression, summarization hooks
        (Section 14) -- see ContextBuilder's docstring for why.
      - MessagePack / other binary serialization formats (Section 16)
        -- JSON (via pydantic's own model_dump_json /
        model_validate_json) covers V1's needs without a new
        dependency; adding a binary format is a clean, separable
        future task.
      - Context expiration / archival lifecycle (Section 12: Ready ->
        Consumed -> Archived) -- meaningful once contexts are tracked
        over time by a caller, rather than being built fresh per
        request as they are here.

    Every other subsystem interacts with context aggregation
    exclusively through this service, exactly as KnowledgeService /
    PromptService / WorkflowService / ModelService / ToolService /
    MemoryService are the sole entry points for their engines.
    """

    def __init__(self) -> None:

        super().__init__(name="context_service")

        self._builder = ContextBuilder()

        self._last_sources: set[ContextSource] = set()

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
        Dispose the service.
        """

        self._last_sources.clear()

        self._set_state(ComponentState.DISPOSED)

    # ------------------------------------------------------------------
    # Validation / construction
    # ------------------------------------------------------------------

    def validate(
        self,
        fragments: list[ContextFragment],
        max_fragments: int | None = None,
    ) -> ContextValidationReport:
        """
        Validate fragments without building a PlatformContext.
        """

        return self._builder.validate(fragments, max_fragments=max_fragments)

    def build(
        self,
        fragments: list[ContextFragment],
        max_fragments: int | None = None,
    ) -> PlatformContext:
        """
        Assemble fragments into a single, immutable PlatformContext.

        Raises ValueError if validation finds any error-level issue.
        """

        context = self._builder.build(fragments, max_fragments=max_fragments)

        self._last_sources = {fragment.source for fragment in fragments}

        return context

    def merge(
        self,
        base: PlatformContext,
        override: PlatformContext,
    ) -> PlatformContext:
        """
        Merge two already-built contexts, with `override` taking
        precedence over `base` wherever they define the same slot.

        Implemented by converting both back into fragments and
        re-running them through the same builder logic, rather than a
        separate merge algorithm -- `override`'s fragments are given a
        higher priority than `base`'s, so the same (category, label)
        conflict resolution ContextBuilder already implements decides
        the outcome.
        """

        base_fragments = self._context_to_fragments(base, priority=0)

        override_fragments = self._context_to_fragments(
            override,
            priority=1,
        )

        return self._builder.build(base_fragments + override_fragments)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @staticmethod
    def serialize(context: PlatformContext) -> str:
        """
        Serialize a PlatformContext to a JSON string.
        """

        return context.model_dump_json()

    @staticmethod
    def deserialize(data: str) -> PlatformContext:
        """
        Deserialize a PlatformContext from a JSON string.
        """

        return PlatformContext.model_validate_json(data)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_sources(self) -> list[str]:
        """
        Return the sources that contributed to the most recently
        built context (empty if none has been built yet).
        """

        return sorted(source.value for source in self._last_sources)

    def statistics(self, context: PlatformContext) -> dict[str, Any]:
        """
        Return summary statistics about a PlatformContext.
        """

        per_category = {
            category.value: len(
                getattr(context, field_name)
            )
            for category, field_name in _CATEGORY_FIELD_NAMES.items()
        }

        return {
            "context_id": context.context_id,
            "total_entries": sum(per_category.values()),
            "entries_per_category": per_category,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _context_to_fragments(
        context: PlatformContext,
        priority: int,
    ) -> list[ContextFragment]:

        fragments: list[ContextFragment] = []

        for category, field_name in _CATEGORY_FIELD_NAMES.items():

            bucket: dict[str, Any] = getattr(context, field_name)

            for label, content in bucket.items():

                fragments.append(
                    ContextFragment(
                        source=ContextSource.CUSTOM,
                        category=category,
                        label=label,
                        content=content,
                        priority=priority,
                    )
                )

        return fragments