"""
Knowledge graph.
"""

from __future__ import annotations

from enterprise_ai_platform.knowledge_engine.models import KnowledgeGraphEdge


class KnowledgeGraph:
    """
    An in-memory, queryable graph of (subject, predicate, object)
    edges -- the knowledge domains' relationships instantiated with
    real entities, as opposed to a formal ontology definition.

    Built once via GraphBuilder and held immutable in memory; adjacency
    indices are built at construction time so neighbors() / incoming()
    / traverse() are simple dict lookups rather than repeated scans.
    """

    def __init__(self, edges: list[KnowledgeGraphEdge]) -> None:

        self._edges = list(edges)

        self._outgoing: dict[str, list[KnowledgeGraphEdge]] = {}

        self._incoming: dict[str, list[KnowledgeGraphEdge]] = {}

        for edge in self._edges:

            self._outgoing.setdefault(edge.subject, []).append(edge)

            self._incoming.setdefault(edge.object, []).append(edge)

    @property
    def edges(self) -> list[KnowledgeGraphEdge]:
        """
        Return all edges in the graph.
        """

        return list(self._edges)

    def edge_count(self) -> int:
        """
        Return the number of edges in the graph.
        """

        return len(self._edges)

    def entities(self) -> list[str]:
        """
        Return every distinct entity (subject or object) in the graph.
        """

        found = set(self._outgoing) | set(self._incoming)

        return sorted(found)

    def neighbors(
        self,
        entity: str,
        predicate: str | None = None,
    ) -> list[KnowledgeGraphEdge]:
        """
        Return outgoing edges from `entity`, optionally filtered to a
        single predicate.
        """

        edges = self._outgoing.get(entity, [])

        if predicate is not None:
            edges = [edge for edge in edges if edge.predicate == predicate]

        return edges

    def incoming(
        self,
        entity: str,
        predicate: str | None = None,
    ) -> list[KnowledgeGraphEdge]:
        """
        Return incoming edges to `entity`, optionally filtered to a
        single predicate.
        """

        edges = self._incoming.get(entity, [])

        if predicate is not None:
            edges = [edge for edge in edges if edge.predicate == predicate]

        return edges

    def find(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        object: str | None = None,
    ) -> list[KnowledgeGraphEdge]:
        """
        Return every edge matching the given triple pattern. Any of
        subject / predicate / object left as None matches anything.
        """

        results = self._edges

        if subject is not None:
            results = [edge for edge in results if edge.subject == subject]

        if predicate is not None:
            results = [
                edge for edge in results if edge.predicate == predicate
            ]

        if object is not None:
            results = [edge for edge in results if edge.object == object]

        return results

    def traverse(
        self,
        start_entity: str,
        max_depth: int = 2,
    ) -> list[KnowledgeGraphEdge]:
        """
        Breadth-first traversal of outgoing edges from `start_entity`,
        up to `max_depth` hops. Returns every edge encountered.
        """

        visited_edges: list[KnowledgeGraphEdge] = []

        seen_entities = {start_entity}

        frontier = [start_entity]

        for _ in range(max_depth):

            next_frontier: list[str] = []

            for entity in frontier:

                for edge in self._outgoing.get(entity, []):

                    visited_edges.append(edge)

                    if edge.object not in seen_entities:
                        seen_entities.add(edge.object)
                        next_frontier.append(edge.object)

            frontier = next_frontier

            if not frontier:
                break

        return visited_edges