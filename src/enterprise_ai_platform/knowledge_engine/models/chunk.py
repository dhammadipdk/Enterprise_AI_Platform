"""
Knowledge chunk.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Chunk(BaseModel):
    """
    One retrievable unit of knowledge content, produced by chunking
    an asset for downstream embedding and retrieval.
    """

    model_config = ConfigDict(frozen=True)

    content: str

    repository: str

    domain: str

    asset: str

    chunk_index: int

    metadata: dict[str, Any] = {}
    
    