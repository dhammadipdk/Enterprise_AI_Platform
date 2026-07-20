"""
Chunking strategy registry.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base import BaseRegistry
from enterprise_ai_platform.knowledge_engine.chunking.base_chunking_strategy import (
    BaseChunkingStrategy,
)


class ChunkingStrategyRegistry(BaseRegistry[BaseChunkingStrategy]):
    """
    Registry of chunking strategies, keyed by file extension
    (for example ".csv", ".md").
    """

    pass