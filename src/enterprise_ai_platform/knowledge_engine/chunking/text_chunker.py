"""
Text chunking strategy.
"""

from __future__ import annotations

from enterprise_ai_platform.knowledge_engine.chunking.base_chunking_strategy import (
    BaseChunkingStrategy,
)
from enterprise_ai_platform.knowledge_engine.models import Chunk


class TextChunker(BaseChunkingStrategy):
    """
    Splits raw text into overlapping, fixed-size character windows.

    Suited to markdown / free-text assets such as domain READMEs.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size "
                f"(got chunk_size={chunk_size}, "
                f"chunk_overlap={chunk_overlap})."
            )

        self._chunk_size = chunk_size

        self._chunk_overlap = chunk_overlap

    def chunk(
        self,
        content: str,
        repository: str,
        domain: str,
        asset: str,
    ) -> list[Chunk]:

        if not content:
            return []

        step = self._chunk_size - self._chunk_overlap

        chunks: list[Chunk] = []

        start = 0

        index = 0

        while start < len(content):

            end = min(start + self._chunk_size, len(content))

            chunks.append(
                Chunk(
                    content=content[start:end],
                    repository=repository,
                    domain=domain,
                    asset=asset,
                    chunk_index=index,
                    metadata={
                        "start_offset": start,
                        "end_offset": end,
                    },
                )
            )

            index += 1

            if end == len(content):
                break

            start += step

        return chunks