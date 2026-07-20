"""
Vector store match.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.knowledge_engine.models import Chunk


class VectorStoreMatch(BaseModel):
    """
    One result returned from a vector store similarity query.

    `score` is a similarity score in roughly [0, 1] for cosine space —
    higher means more similar.
    """

    model_config = ConfigDict(frozen=True)

    chunk: Chunk

    score: float