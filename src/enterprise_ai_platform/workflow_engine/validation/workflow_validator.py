"""
Workflow validator.
"""

from __future__ import annotations

from enterprise_ai_platform.workflow_engine.compiler import WorkflowCompiler
from enterprise_ai_platform.workflow_engine.models import (
    NodeType,
    WorkflowDefinition,
)
from enterprise_ai_platform.workflow_engine.validation.workflow_validation_issue import (
    WorkflowValidationIssue,
)
from enterprise_ai_platform.workflow_engine.validation.workflow_validation_report import (
    WorkflowValidationReport,
)


class WorkflowValidator:
    """
    Extends WorkflowCompiler's mandatory structural checks with
    softer, quality-oriented checks that don't block compilation but
    flag likely authoring mistakes -- the same relationship
    RepositoryValidator has to RepositoryLoader in the Knowledge
    Engine, adapted to the fact that WorkflowCompiler already enforces
    real structural rules as a mandatory gate (unlike RepositoryLoader,
    which had none originally).

    Composes WorkflowCompiler.validate() rather than reimplementing
    its checks, so there remains exactly one place that decides
    whether a workflow's structure is valid; this only adds to that
    report.

    Deliberately not implemented: checking whether an edge's condition
    names a variable some upstream node will actually produce. That
    would require knowing initial_variables, which aren't supplied
    until execute() time -- a condition may legitimately reference a
    variable provided at execution rather than one produced by any
    node, so this check would have unavoidable false positives if run
    at validation time.
    """

    def __init__(self) -> None:

        self._compiler = WorkflowCompiler()

    def validate(
        self,
        definition: WorkflowDefinition,
    ) -> WorkflowValidationReport:
        """
        Run WorkflowCompiler's structural checks plus this validator's
        additional quality checks against a definition.
        """

        issues: list[WorkflowValidationIssue] = list(
            self._compiler.validate(definition).issues
        )

        issues.extend(self._check_retry_policies(definition))

        issues.extend(self._check_timeouts(definition))

        issues.extend(self._check_wait_node_configuration(definition))

        issues.extend(self._check_decision_node_outputs(definition))

        issues.extend(self._check_duplicate_edges(definition))

        issues.extend(self._check_start_end_configuration(definition))

        return WorkflowValidationReport(issues=issues)

    @staticmethod
    def _check_retry_policies(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        issues: list[WorkflowValidationIssue] = []

        for node in definition.nodes:

            if node.retry_policy is None:
                continue

            if node.retry_policy.max_attempts < 1:
                issues.append(
                    WorkflowValidationIssue(
                        severity="error",
                        code="INVALID_RETRY_POLICY",
                        message=(
                            f"Node '{node.id}' has "
                            f"max_attempts="
                            f"{node.retry_policy.max_attempts}; must "
                            f"be at least 1."
                        ),
                    )
                )

            if node.retry_policy.backoff_seconds < 0:
                issues.append(
                    WorkflowValidationIssue(
                        severity="error",
                        code="INVALID_RETRY_POLICY",
                        message=(
                            f"Node '{node.id}' has a negative "
                            f"backoff_seconds "
                            f"({node.retry_policy.backoff_seconds})."
                        ),
                    )
                )

        return issues

    @staticmethod
    def _check_timeouts(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        issues: list[WorkflowValidationIssue] = []

        for node in definition.nodes:

            if node.timeout_seconds is None:
                continue

            if node.timeout_seconds < 0:
                issues.append(
                    WorkflowValidationIssue(
                        severity="error",
                        code="INVALID_TIMEOUT",
                        message=(
                            f"Node '{node.id}' has a negative "
                            f"timeout_seconds "
                            f"({node.timeout_seconds})."
                        ),
                    )
                )

            elif node.timeout_seconds == 0:
                issues.append(
                    WorkflowValidationIssue(
                        severity="warning",
                        code="ZERO_TIMEOUT",
                        message=(
                            f"Node '{node.id}' has timeout_seconds=0, "
                            f"which is ambiguous (immediate timeout "
                            f"vs. no timeout)."
                        ),
                    )
                )

        return issues

    @staticmethod
    def _check_wait_node_configuration(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        return [
            WorkflowValidationIssue(
                severity="warning",
                code="WAIT_NODE_NO_DURATION",
                message=(
                    f"Wait node '{node.id}' has no duration_seconds "
                    f"configured; it will not actually wait."
                ),
            )
            for node in definition.nodes
            if node.node_type == NodeType.WAIT
            and not node.configuration.get("duration_seconds")
        ]

    @staticmethod
    def _check_decision_node_outputs(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        return [
            WorkflowValidationIssue(
                severity="warning",
                code="DECISION_NODE_NO_OUTPUTS",
                message=(
                    f"Decision node '{node.id}' declares no outputs; "
                    f"downstream edge conditions have nothing to "
                    f"check."
                ),
            )
            for node in definition.nodes
            if node.node_type == NodeType.DECISION and not node.outputs
        ]

    @staticmethod
    def _check_duplicate_edges(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        seen: set[tuple[str, str, str | None]] = set()

        duplicates: list[tuple[str, str, str | None]] = []

        for edge in definition.edges:

            key = (edge.source, edge.destination, edge.condition)

            if key in seen:
                duplicates.append(key)

            seen.add(key)

        issues = []

        for source, destination, condition in duplicates:

            condition_clause = (
                f" with condition '{condition}'" if condition else ""
            )

            issues.append(
                WorkflowValidationIssue(
                    severity="warning",
                    code="DUPLICATE_EDGE",
                    message=(
                        f"Duplicate edge from '{source}' to "
                        f"'{destination}'{condition_clause}."
                    ),
                )
            )

        return issues

    @staticmethod
    def _check_start_end_configuration(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        issues: list[WorkflowValidationIssue] = []

        for node in definition.nodes:

            if node.node_type not in (NodeType.START, NodeType.END):
                continue

            if node.retry_policy is not None:
                issues.append(
                    WorkflowValidationIssue(
                        severity="warning",
                        code="INEFFECTIVE_RETRY_POLICY",
                        message=(
                            f"Node '{node.id}' is a "
                            f"{node.node_type.value} node; "
                            f"retry_policy has no effect."
                        ),
                    )
                )

            if node.timeout_seconds is not None:
                issues.append(
                    WorkflowValidationIssue(
                        severity="warning",
                        code="INEFFECTIVE_TIMEOUT",
                        message=(
                            f"Node '{node.id}' is a "
                            f"{node.node_type.value} node; "
                            f"timeout_seconds has no effect."
                        ),
                    )
                )

        return issues