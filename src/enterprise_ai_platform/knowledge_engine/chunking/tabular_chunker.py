"""
Tabular chunking strategy.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.knowledge_engine.chunking.base_chunking_strategy import (
    BaseChunkingStrategy,
)
from enterprise_ai_platform.knowledge_engine.models import Chunk


class TabularChunker(BaseChunkingStrategy):
    """
    Splits tabular content (CSV rows) into one chunk per row.

    Each row is rendered as "column: value" lines so it reads as a
    coherent piece of text for embedding, rather than a raw CSV row.
    """

    def chunk(
        self,
        content: list[dict[str, Any]],
        repository: str,
        domain: str,
        asset: str,
    ) -> list[Chunk]:

        chunks: list[Chunk] = []

        for index, row in enumerate(content):

            rendered = "\n".join(
                f"{key}: {value}" for key, value in row.items()
            )

            chunks.append(
                Chunk(
                    content=rendered,
                    repository=repository,
                    domain=domain,
                    asset=asset,
                    chunk_index=index,
                    metadata=dict(row),
                )
            )

        return chunks