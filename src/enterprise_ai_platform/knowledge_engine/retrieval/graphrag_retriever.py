"""
GraphRAG retriever.
"""

from __future__ import annotations

from typing import Callable

from enterprise_ai_platform.knowledge_engine.graph.knowledge_graph import (
    KnowledgeGraph,
)
from enterprise_ai_platform.knowledge_engine.models import KnowledgeGraphEdge
from enterprise_ai_platform.knowledge_engine.retrieval.context_formatting import (
    format_chunk_matches,
)
from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


SearchFunction = Callable[..., list[VectorStoreMatch]]
GraphProviderFunction = Callable[[str], KnowledgeGraph]


class GraphRAGRetriever:
    """
    Augments hybrid (semantic + keyword) retrieval with directly
    connected facts pulled from the knowledge graph.

    Given a query:
      1. Runs hybrid search to find relevant chunks (unchanged).
      2. Looks for known graph entities mentioned in the query text
         *or* in the content of the chunks hybrid search already found
         relevant -- grounding entity matching in what retrieval
         already proved relevant, rather than requiring the user's own
         phrasing to hit an exact entity identifier.
      3. Traverses the graph outward from each matched entity, up to a
         configurable depth.
      4. Appends the traversed edges as a deterministic "Related
         facts" block after the chunk context.

    Every graph fact surfaced is a literal (subject, predicate, object)
    edge, not a paraphrase or an LLM guess -- kept fully explainable.

    If no knowledge graph has been built for a repository yet, this
    degrades transparently to chunk-only context rather than failing;
    graph augmentation is a strict enhancement, never a hard
    requirement, since not every repository will have relationship
    data yet.

    Depends on injected callables (typically
    KnowledgeService.hybrid_search and KnowledgeService.
    get_knowledge_graph), not on KnowledgeService itself, matching
    Retriever / HybridRetriever's approach.
    """

    def __init__(
        self,
        hybrid_search_fn: SearchFunction,
        graph_provider_fn: GraphProviderFunction,
        traversal_depth: int = 1,
    ) -> None:

        self._hybrid_search_fn = hybrid_search_fn

        self._graph_provider_fn = graph_provider_fn

        self._traversal_depth = traversal_depth

    @property
    def traversal_depth(self) -> int:
        """
        Return the configured graph traversal depth.
        """

        return self._traversal_depth

    def retrieve_context(
        self,
        repository: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> str:
        """
        Return a prompt-ready context block combining hybrid retrieval
        with connected knowledge graph facts, if a graph exists for
        this repository.
        """

        chunk_matches = self._hybrid_search_fn(
            repository,
            query_text,
            top_k=top_k,
            domain=domain,
        )

        chunk_context = format_chunk_matches(chunk_matches)

        graph_context = self._build_graph_context(
            repository,
            query_text,
            chunk_matches,
        )

        sections = [
            section for section in (chunk_context, graph_context) if section
        ]

        return "\n\n".join(sections)

    def _build_graph_context(
        self,
        repository: str,
        query_text: str,
        chunk_matches: list[VectorStoreMatch],
    ) -> str:

        try:
            graph = self._graph_provider_fn(repository)
        except KeyError:
            return ""

        searchable_text = " ".join(
            [query_text] + [match.chunk.content for match in chunk_matches]
        )

        matched_entities = self._match_entities(
            searchable_text,
            graph.entities(),
        )

        edges: list[KnowledgeGraphEdge] = []

        for entity in matched_entities:
            edges.extend(
                graph.traverse(entity, max_depth=self._traversal_depth)
            )

        return self._format_edges(edges)

    @staticmethod
    def _match_entities(text: str, entities: list[str]) -> list[str]:

        lowered_text = text.lower()

        return [
            entity for entity in entities if entity.lower() in lowered_text
        ]

    @staticmethod
    def _format_edges(edges: list[KnowledgeGraphEdge]) -> str:

        if not edges:
            return ""

        seen: set[tuple[str, str, str]] = set()

        deduped: list[KnowledgeGraphEdge] = []

        for edge in edges:

            key = (edge.subject, edge.predicate, edge.object)

            if key in seen:
                continue

            seen.add(key)

            deduped.append(edge)

        lines = [
            f"- {edge.subject} {edge.predicate} {edge.object}"
            for edge in deduped
        ]

        return "Related facts (from knowledge graph):\n" + "\n".join(lines)