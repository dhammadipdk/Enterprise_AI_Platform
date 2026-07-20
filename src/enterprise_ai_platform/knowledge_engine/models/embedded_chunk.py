"""
Embedded chunk.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.knowledge_engine.models.chunk import Chunk


class EmbeddedChunk(BaseModel):
    """
    A Chunk paired with its vector embedding.
    """

    model_config = ConfigDict(frozen=True)

    chunk: Chunk

    vector: list[float]

    provider: str