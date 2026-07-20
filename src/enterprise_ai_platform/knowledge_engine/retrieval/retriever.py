"""
Retriever.
"""

from __future__ import annotations

from typing import Callable

from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


SearchFunction = Callable[..., list[VectorStoreMatch]]


class Retriever:
    """
    Turns raw vector search results into retrieval results ready for
    downstream consumers (Prompt Engine, applications), by applying a
    minimum relevance threshold and formatting matches into a single
    prompt-ready context block.

    Depends only on a search callable (typically
    KnowledgeService.search), not on KnowledgeService itself -- this
    keeps the class independently testable and avoids a circular
    dependency between the service and the component it composes.
    """

    def __init__(
        self,
        search_fn: SearchFunction,
        score_threshold: float = 0.0,
    ) -> None:

        self._search_fn = search_fn

        self._score_threshold = score_threshold

    @property
    def score_threshold(self) -> float:
        """
        Return the configured minimum relevance score.
        """

        return self._score_threshold

    def retrieve(
        self,
        repository: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[VectorStoreMatch]:
        """
        Return relevant matches above the configured score threshold.
        """

        matches = self._search_fn(
            repository,
            query_text,
            top_k=top_k,
            domain=domain,
        )

        return [
            match
            for match in matches
            if match.score >= self._score_threshold
        ]

    def retrieve_as_context(
        self,
        repository: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> str:
        """
        Retrieve matches and render them into a single text block
        suitable for injecting into a prompt.

        Returns an empty string if nothing meets the score threshold.
        """

        matches = self.retrieve(
            repository,
            query_text,
            top_k=top_k,
            domain=domain,
        )

        return self._format_context(matches)

    @staticmethod
    def _format_context(matches: list[VectorStoreMatch]) -> str:

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