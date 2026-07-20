"""
Knowledge embedding.
"""

from enterprise_ai_platform.knowledge_engine.embedding.base_embedding_provider import (
    BaseEmbeddingProvider,
)
from enterprise_ai_platform.knowledge_engine.embedding.embedding_pipeline import (
    EmbeddingPipeline,
)
from enterprise_ai_platform.knowledge_engine.embedding.local_embedding_provider import (
    LocalEmbeddingProvider,
)

__all__ = [
    "BaseEmbeddingProvider",
    "EmbeddingPipeline",
    "LocalEmbeddingProvider",
]