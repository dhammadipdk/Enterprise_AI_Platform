"""
Knowledge graph registry.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base import BaseRegistry
from enterprise_ai_platform.knowledge_engine.graph.knowledge_graph import (
    KnowledgeGraph,
)


class KnowledgeGraphRegistry(BaseRegistry[KnowledgeGraph]):
    """
    Registry of knowledge graphs, keyed by repository name.
    """

    pass