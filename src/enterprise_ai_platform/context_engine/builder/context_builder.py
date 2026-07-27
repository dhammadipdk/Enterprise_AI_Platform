"""
Context builder.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from enterprise_ai_platform.context_engine.models import (
    ContextCategory,
    ContextFragment,
    PlatformContext,
)
from enterprise_ai_platform.context_engine.validation import (
    ContextValidationIssue,
    ContextValidationReport,
)


class ContextBuilder:
    """
    Collects ContextFragments and assembles them into a single,
    immutable PlatformContext (Section 11 of the frozen spec: Collect
    Fragments, Validate, Merge, Deduplicate, Optimize, Construct).

    Fragments sharing the same (category, label) are resolved by
    priority: the highest-priority fragment's content wins that slot.
    Among equal priorities, the fragment appearing later in the input
    list wins -- a deterministic, if arbitrary, tie-break, since two
    equal-priority fragments genuinely disagreeing on the same slot
    has no principled "correct" answer; this is surfaced as a warning
    during validate() rather than silently resolved without a trace.

    "Deduplicate" (Section 11/14) is handled by this same (category,
    label) keying, not as a separate pass: two fragments claiming the
    same slot is exactly the situation the priority mechanism already
    resolves.

    Token-aware compression, summarization hooks, and semantic
    compression (Section 14) are deliberately not implemented here --
    those require knowing what the assembled context will actually be
    used for (a specific prompt's token budget), which this generic
    builder has no visibility into. Basic size limiting (max fragment
    count) is included since it needs no such visibility.
    """

    def build(
        self,
        fragments: list[ContextFragment],
        max_fragments: int | None = None,
    ) -> PlatformContext:
        """
        Validate and assemble `fragments` into a PlatformContext.

        Raises ValueError if validation finds any error-level issue
        (empty labels, or more fragments than max_fragments allows).
        """

        report = self.validate(fragments, max_fragments=max_fragments)

        if not report.is_valid:
            error_messages = "; ".join(
                issue.message for issue in report.errors
            )
            raise ValueError(
                f"Cannot build context: {error_messages}"
            )

        buckets = self._merge_fragments(fragments)

        return PlatformContext(
            workflow_context=buckets[ContextCategory.WORKFLOW],
            knowledge_context=buckets[ContextCategory.KNOWLEDGE],
            memory_context=buckets[ContextCategory.MEMORY],
            user_context=buckets[ContextCategory.USER],
            execution_context=buckets[ContextCategory.EXECUTION],
            tool_context=buckets[ContextCategory.TOOL],
            model_context=buckets[ContextCategory.MODEL],
        )

    def validate(
        self,
        fragments: list[ContextFragment],
        max_fragments: int | None = None,
    ) -> ContextValidationReport:
        """
        Validate fragments without building a PlatformContext.
        """

        issues: list[ContextValidationIssue] = []

        issues.extend(self._check_empty_labels(fragments))

        issues.extend(self._check_max_fragments(fragments, max_fragments))

        issues.extend(self._check_priority_ties(fragments))

        return ContextValidationReport(issues=issues)

    def _merge_fragments(
        self,
        fragments: list[ContextFragment],
    ) -> dict[ContextCategory, dict[str, Any]]:

        buckets: dict[ContextCategory, dict[str, Any]] = {
            category: {} for category in ContextCategory
        }

        winning_priority: dict[tuple[ContextCategory, str], int] = {}

        for fragment in sorted(fragments, key=lambda f: f.priority):

            key = (fragment.category, fragment.label)

            current = winning_priority.get(key)

            if current is None or fragment.priority >= current:
                buckets[fragment.category][fragment.label] = fragment.content
                winning_priority[key] = fragment.priority

        return buckets

    @staticmethod
    def _check_empty_labels(
        fragments: list[ContextFragment],
    ) -> list[ContextValidationIssue]:

        return [
            ContextValidationIssue(
                severity="error",
                code="EMPTY_FRAGMENT_LABEL",
                message=(
                    f"Fragment '{fragment.fragment_id}' has an empty "
                    f"label."
                ),
            )
            for fragment in fragments
            if not fragment.label or not fragment.label.strip()
        ]

    @staticmethod
    def _check_max_fragments(
        fragments: list[ContextFragment],
        max_fragments: int | None,
    ) -> list[ContextValidationIssue]:

        if max_fragments is None or len(fragments) <= max_fragments:
            return []

        return [
            ContextValidationIssue(
                severity="error",
                code="OVERSIZED_CONTEXT",
                message=(
                    f"{len(fragments)} fragments exceeds the maximum "
                    f"of {max_fragments}."
                ),
            )
        ]

    @staticmethod
    def _check_priority_ties(
        fragments: list[ContextFragment],
    ) -> list[ContextValidationIssue]:

        grouped: dict[tuple[ContextCategory, str], list[ContextFragment]] = (
            defaultdict(list)
        )

        for fragment in fragments:
            grouped[(fragment.category, fragment.label)].append(fragment)

        issues: list[ContextValidationIssue] = []

        for (category, label), group in grouped.items():

            if len(group) < 2:
                continue

            max_priority = max(f.priority for f in group)

            tied = [f for f in group if f.priority == max_priority]

            distinct_contents = {repr(f.content) for f in tied}

            if len(tied) > 1 and len(distinct_contents) > 1:
                issues.append(
                    ContextValidationIssue(
                        severity="warning",
                        code="UNRESOLVED_PRIORITY_TIE",
                        message=(
                            f"{len(tied)} fragments tie for category "
                            f"'{category.value}', label '{label}' at "
                            f"priority {max_priority} with different "
                            f"content; the last one in input order "
                            f"was used."
                        ),
                    )
                )

        return issues