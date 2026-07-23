"""
Shared context formatting helpers for retrieval strategies.
"""

from __future__ import annotations

from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


def format_chunk_matches(matches: list[VectorStoreMatch]) -> str:
    """
    Render a list of VectorStoreMatch results into a single numbered,
    sourced text block suitable for injecting into a prompt.

    Shared by Retriever and GraphRAGRetriever so both produce
    identically formatted chunk context.
    """

    if not matches:
        return ""

    blocks: list[str] = []

    for index, match in enumerate(matches, start=1):

        source = f"{match.chunk.domain}/{match.chunk.asset}"

        blocks.append(
            f"[{index}] (source: {source}, score: {match.score:.2f})\n"
            f"{match.chunk.content}"
        )

    return "\n\n".join(blocks)