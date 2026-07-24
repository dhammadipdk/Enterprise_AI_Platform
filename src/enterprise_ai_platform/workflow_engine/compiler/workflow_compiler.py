"""
Workflow compiler.
"""

from __future__ import annotations

from enterprise_ai_platform.workflow_engine.graph import WorkflowGraph
from enterprise_ai_platform.workflow_engine.models import (
    NodeType,
    WorkflowDefinition,
)
from enterprise_ai_platform.workflow_engine.validation import (
    WorkflowValidationIssue,
    WorkflowValidationReport,
)


class WorkflowCompiler:
    """
    Compiles a WorkflowDefinition into an immutable, traversable
    WorkflowGraph.

    Enforces the frozen spec's Section 16 structural rules, plus one
    addition found while designing the later, separate
    WorkflowValidator: duplicate node ids. Nothing previously detected
    this -- every id-keyed dict built downstream (entry-node lookup,
    cycle detection, WorkflowGraph._nodes_by_id) would silently keep
    only the last node sharing an id, so a workflow with a duplicate
    id could compile "successfully" today with nodes quietly dropped.
    This is a structural correctness issue, not a soft quality check,
    so it belongs here rather than only in the validator layer.

      - no duplicate node ids
      - exactly one Start node
      - at least one End node
      - entry_node references a real node, and that node is a Start
        node
      - every edge's source/destination references a real node
      - no isolated nodes (unless the workflow has only one node)
      - no cycles, unless the cycle passes through a Loop-type node
        -- Loop is the spec's explicit mechanism for intentional
        repetition (Section 10), so a cycle is only "allowed" when
        it's the mechanism actually meant to produce one.

    Known limitation, accepted for V1: in a complex graph with several
    back-edges into the same strongly-connected component, more than
    one issue may be reported for what is structurally a single
    underlying cycle. Over-reporting was chosen over the added
    complexity of de-duplicating overlapping cycle paths.
    """

    def validate(
        self,
        definition: WorkflowDefinition,
    ) -> WorkflowValidationReport:
        """
        Run all structural validation checks against a definition.
        """

        issues: list[WorkflowValidationIssue] = []

        issues.extend(self._check_duplicate_node_ids(definition))

        issues.extend(self._check_start_node_count(definition))

        issues.extend(self._check_end_node_count(definition))

        issues.extend(self._check_entry_node(definition))

        issues.extend(self._check_edge_references(definition))

        issues.extend(self._check_isolated_nodes(definition))

        issues.extend(self._check_cycles(definition))

        return WorkflowValidationReport(issues=issues)

    def compile(self, definition: WorkflowDefinition) -> WorkflowGraph:
        """
        Validate and compile a definition into an immutable graph.

        Raises ValueError if any error-level validation issue is
        found.
        """

        report = self.validate(definition)

        if not report.is_valid:

            error_messages = "; ".join(
                issue.message for issue in report.errors
            )

            raise ValueError(
                f"Cannot compile workflow '{definition.name}': "
                f"{error_messages}"
            )

        return WorkflowGraph(
            name=definition.name,
            version=definition.version,
            entry_node=definition.entry_node,
            nodes=definition.nodes,
            edges=definition.edges,
            metadata=definition.metadata,
        )

    @staticmethod
    def _check_duplicate_node_ids(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        seen: set[str] = set()

        duplicates: set[str] = set()

        for node in definition.nodes:

            if node.id in seen:
                duplicates.add(node.id)

            seen.add(node.id)

        return [
            WorkflowValidationIssue(
                severity="error",
                code="DUPLICATE_NODE_ID",
                message=f"More than one node has id '{node_id}'.",
            )
            for node_id in sorted(duplicates)
        ]

    @staticmethod
    def _check_start_node_count(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        start_nodes = [
            node for node in definition.nodes if node.node_type == NodeType.START
        ]

        if len(start_nodes) == 1:
            return []

        return [
            WorkflowValidationIssue(
                severity="error",
                code="INVALID_START_NODE_COUNT",
                message=(
                    f"Workflow must have exactly one Start node, found "
                    f"{len(start_nodes)}."
                ),
            )
        ]

    @staticmethod
    def _check_end_node_count(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        end_nodes = [
            node for node in definition.nodes if node.node_type == NodeType.END
        ]

        if len(end_nodes) >= 1:
            return []

        return [
            WorkflowValidationIssue(
                severity="error",
                code="MISSING_END_NODE",
                message="Workflow must have at least one End node.",
            )
        ]

    @staticmethod
    def _check_entry_node(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        nodes_by_id = {node.id: node for node in definition.nodes}

        if definition.entry_node not in nodes_by_id:
            return [
                WorkflowValidationIssue(
                    severity="error",
                    code="INVALID_ENTRY_NODE",
                    message=(
                        f"entry_node '{definition.entry_node}' does not "
                        f"reference any node in this workflow."
                    ),
                )
            ]

        entry = nodes_by_id[definition.entry_node]

        if entry.node_type != NodeType.START:
            return [
                WorkflowValidationIssue(
                    severity="error",
                    code="ENTRY_NODE_NOT_START",
                    message=(
                        f"entry_node '{definition.entry_node}' must be "
                        f"a Start node, but is "
                        f"'{entry.node_type.value}'."
                    ),
                )
            ]

        return []

    @staticmethod
    def _check_edge_references(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        node_ids = {node.id for node in definition.nodes}

        issues: list[WorkflowValidationIssue] = []

        for edge in definition.edges:

            if edge.source not in node_ids:
                issues.append(
                    WorkflowValidationIssue(
                        severity="error",
                        code="INVALID_EDGE_REFERENCE",
                        message=(
                            f"Edge references unknown source node "
                            f"'{edge.source}'."
                        ),
                    )
                )

            if edge.destination not in node_ids:
                issues.append(
                    WorkflowValidationIssue(
                        severity="error",
                        code="INVALID_EDGE_REFERENCE",
                        message=(
                            f"Edge references unknown destination node "
                            f"'{edge.destination}'."
                        ),
                    )
                )

        return issues

    @staticmethod
    def _check_isolated_nodes(
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        if len(definition.nodes) <= 1:
            return []

        touched: set[str] = set()

        for edge in definition.edges:
            touched.add(edge.source)
            touched.add(edge.destination)

        return [
            WorkflowValidationIssue(
                severity="error",
                code="ISOLATED_NODE",
                message=(
                    f"Node '{node.id}' has no edges connecting it to "
                    f"the rest of the workflow."
                ),
            )
            for node in definition.nodes
            if node.id not in touched
        ]

    def _check_cycles(
        self,
        definition: WorkflowDefinition,
    ) -> list[WorkflowValidationIssue]:

        node_ids = {node.id for node in definition.nodes}

        node_types = {node.id: node.node_type for node in definition.nodes}

        adjacency: dict[str, list[str]] = {}

        for edge in definition.edges:

            if edge.source in node_ids and edge.destination in node_ids:
                adjacency.setdefault(edge.source, []).append(
                    edge.destination
                )

        issues: list[WorkflowValidationIssue] = []

        visited: set[str] = set()

        def _dfs(node_id: str, path: list[str], in_stack: set[str]) -> None:

            visited.add(node_id)

            in_stack.add(node_id)

            path.append(node_id)

            for neighbor in adjacency.get(node_id, []):

                if neighbor in in_stack:

                    cycle_start = path.index(neighbor)

                    cycle_nodes = path[cycle_start:] + [neighbor]

                    if not any(
                        node_types.get(candidate) == NodeType.LOOP
                        for candidate in cycle_nodes
                    ):
                        issues.append(
                            WorkflowValidationIssue(
                                severity="error",
                                code="ILLEGAL_CYCLE",
                                message=(
                                    f"Workflow contains a cycle not "
                                    f"passing through a Loop node: "
                                    f"{' -> '.join(cycle_nodes)}."
                                ),
                            )
                        )

                elif neighbor not in visited:
                    _dfs(neighbor, path, in_stack)

            path.pop()

            in_stack.remove(node_id)

        for node_id in node_ids:

            if node_id not in visited:
                _dfs(node_id, [], set())

        return issues