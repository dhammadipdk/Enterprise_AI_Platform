"""
Knowledge graph edge.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class KnowledgeGraphEdge(BaseModel):
    """
    One (subject, predicate, object) triple in the knowledge graph,
    with provenance back to the domain and asset it came from.
    """

    model_config = ConfigDict(frozen=True)

    subject: str

    predicate: str

    object: str

    domain: str

    source_asset: str