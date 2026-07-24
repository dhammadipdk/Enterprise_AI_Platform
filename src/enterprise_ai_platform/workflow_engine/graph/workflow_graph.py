"""
Workflow graph.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.workflow_engine.models import (
    WorkflowEdge,
    WorkflowNode,
)


class WorkflowGraph:
    """
    A compiled, immutable, traversable execution graph -- produced
    once by WorkflowCompiler and held in memory. Adjacency indices are
    built at construction time (Section 12: "optimized for runtime"),
    so outgoing_edges() / get_node() are dict lookups rather than
    repeated scans over the node/edge lists, matching KnowledgeGraph's
    approach in the Knowledge Engine.
    """

    def __init__(
        self,
        name: str,
        version: str,
        entry_node: str,
        nodes: list[WorkflowNode],
        edges: list[WorkflowEdge],
        metadata: dict[str, Any] | None = None,
    ) -> None:

        self._name = name

        self._version = version

        self._entry_node_id = entry_node

        self._nodes = list(nodes)

        self._edges = list(edges)

        self._metadata = dict(metadata or {})

        self._nodes_by_id = {node.id: node for node in self._nodes}

        self._outgoing: dict[str, list[WorkflowEdge]] = {}

        for edge in self._edges:
            self._outgoing.setdefault(edge.source, []).append(edge)

    @property
    def name(self) -> str:
        """
        Return the workflow's name.
        """

        return self._name

    @property
    def version(self) -> str:
        """
        Return the workflow's version.
        """

        return self._version

    @property
    def entry_node_id(self) -> str:
        """
        Return the id of the workflow's entry node.
        """

        return self._entry_node_id

    @property
    def nodes(self) -> list[WorkflowNode]:
        """
        Return every node in the graph.
        """

        return list(self._nodes)

    @property
    def edges(self) -> list[WorkflowEdge]:
        """
        Return every edge in the graph.
        """

        return list(self._edges)

    @property
    def metadata(self) -> dict[str, Any]:
        """
        Return the workflow's metadata.
        """

        return dict(self._metadata)

    def node_count(self) -> int:
        """
        Return the number of nodes in the graph.
        """

        return len(self._nodes)

    def edge_count(self) -> int:
        """
        Return the number of edges in the graph.
        """

        return len(self._edges)

    def get_node(self, node_id: str) -> WorkflowNode:
        """
        Return a single node by id.
        """

        if node_id not in self._nodes_by_id:
            raise KeyError(
                f"No node with id '{node_id}' in workflow '{self._name}'."
            )

        return self._nodes_by_id[node_id]

    def entry_node(self) -> WorkflowNode:
        """
        Return the workflow's entry node.
        """

        return self.get_node(self._entry_node_id)

    def outgoing_edges(
        self,
        node_id: str,
        sorted_by_priority: bool = True,
    ) -> list[WorkflowEdge]:
        """
        Return the outgoing edges from a node.

        By default, sorted by descending priority -- pre-computed here
        so the Execution task doesn't need to re-sort on every node
        transition when deciding which edge to follow first.
        """

        edges = self._outgoing.get(node_id, [])

        if sorted_by_priority:
            edges = sorted(edges, key=lambda edge: edge.priority, reverse=True)

        return edges