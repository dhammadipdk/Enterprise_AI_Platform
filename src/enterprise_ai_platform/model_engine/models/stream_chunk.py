"""
Stream chunk.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class StreamChunk(BaseModel):
    """
    One piece of a streaming model response (Section 17: Token
    Streaming, Chunk Streaming, Partial Responses).
    """

    model_config = ConfigDict(frozen=True)

    request_id: str

    text: str

    is_final: bool = False

    metadata: dict[str, Any] = {}