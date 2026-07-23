"""
Graph builder.
"""

from __future__ import annotations

from typing import Any, Callable

from enterprise_ai_platform.knowledge_engine.graph.knowledge_graph import (
    KnowledgeGraph,
)
from enterprise_ai_platform.knowledge_engine.models import (
    KnowledgeGraphEdge,
    KnowledgeRepository,
)

ContentLoaderFunction = Callable[[str, str, str], Any]


class GraphBuilder:
    """
    Builds a KnowledgeGraph from a repository's "relationship"-typed
    assets.

    A relationship asset (any asset whose asset_type is "relationship"
    -- inferred by RepositoryLoader from a file literally named
    "relationships", e.g. relationships.csv) is expected to contain
    subject/predicate/object columns, one row per edge, e.g.:

        subject,predicate,object
        Policy,has,Coverage
        Coverage,has,Exclusion
        UsedCar,eligible_for,ComprehensiveInsurance

    Depends on an injected content-loading callable (typically
    KnowledgeService.load_asset_content) rather than the provider
    registry directly, matching Retriever / HybridRetriever's
    dependency-injection approach: independently testable, no
    circular dependency on KnowledgeService.
    """

    def __init__(self, content_loader_fn: ContentLoaderFunction) -> None:

        self._content_loader_fn = content_loader_fn

    def build(
        self,
        repository_name: str,
        repository: KnowledgeRepository,
    ) -> KnowledgeGraph:
        """
        Build a KnowledgeGraph from every relationship-typed asset
        across all domains in the repository.
        """

        edges: list[KnowledgeGraphEdge] = []

        for domain in repository.domains:

            for asset in domain.assets:

                if asset.asset_type != "relationship":
                    continue

                rows = self._content_loader_fn(
                    repository_name,
                    domain.name,
                    asset.name,
                )

                edges.extend(
                    self._rows_to_edges(rows, domain.name, asset.name)
                )

        return KnowledgeGraph(edges)

    @staticmethod
    def _rows_to_edges(
        rows: list[dict[str, Any]],
        domain: str,
        asset: str,
    ) -> list[KnowledgeGraphEdge]:

        edges: list[KnowledgeGraphEdge] = []

        for row in rows:

            try:
                edges.append(
                    KnowledgeGraphEdge(
                        subject=str(row["subject"]),
                        predicate=str(row["predicate"]),
                        object=str(row["object"]),
                        domain=domain,
                        source_asset=asset,
                    )
                )
            except KeyError as error:
                raise ValueError(
                    f"Relationship asset '{asset}' in domain '{domain}' "
                    f"is missing a required column: {error}. Expected "
                    f"columns: subject, predicate, object."
                ) from error

        return edges