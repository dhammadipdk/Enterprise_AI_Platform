"""
Hybrid retriever.
"""

from __future__ import annotations

from typing import Callable

from enterprise_ai_platform.knowledge_engine.models import Chunk
from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


SearchFunction = Callable[..., list[VectorStoreMatch]]


class HybridRetriever:
    """
    Combines dense (semantic/vector) search with sparse (keyword/BM25)
    search using Reciprocal Rank Fusion (RRF).

    RRF combines two rankings by their *position* in each list rather
    than their raw scores, which sidesteps the problem of cosine
    similarity (roughly -1..1) and BM25 scores (unbounded, corpus
    dependent) living on incompatible scales -- the standard choice
    for combining rankings from different scoring systems.

    Depends only on two injected search callables (typically
    KnowledgeService.search and KnowledgeService.keyword_search), not
    on KnowledgeService itself, matching Retriever's approach: fully
    independently testable, no circular dependency.
    """

    def __init__(
        self,
        semantic_search_fn: SearchFunction,
        keyword_search_fn: SearchFunction,
        rrf_k: int = 60,
    ) -> None:

        self._semantic_search_fn = semantic_search_fn

        self._keyword_search_fn = keyword_search_fn

        self._rrf_k = rrf_k

    def retrieve(
        self,
        repository: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
        candidate_pool: int = 20,
    ) -> list[VectorStoreMatch]:
        """
        Return the top_k chunks by fused semantic + keyword rank.
        """

        pool = max(candidate_pool, top_k)

        semantic_results = self._semantic_search_fn(
            repository,
            query_text,
            top_k=pool,
            domain=domain,
        )

        keyword_results = self._keyword_search_fn(
            repository,
            query_text,
            top_k=pool,
            domain=domain,
        )

        fused_scores: dict[str, float] = {}

        chunk_by_id: dict[str, Chunk] = {}

        for result_list in (semantic_results, keyword_results):

            for rank, match in enumerate(result_list, start=1):

                chunk_id = self._chunk_id(match.chunk)

                fused_scores[chunk_id] = fused_scores.get(
                    chunk_id, 0.0
                ) + 1.0 / (self._rrf_k + rank)

                chunk_by_id[chunk_id] = match.chunk

        ranked = sorted(
            fused_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            VectorStoreMatch(chunk=chunk_by_id[chunk_id], score=score)
            for chunk_id, score in ranked[:top_k]
        ]

    @staticmethod
    def _chunk_id(chunk: Chunk) -> str:

        return (
            f"{chunk.repository}:{chunk.domain}:"
            f"{chunk.asset}:{chunk.chunk_index}"
        )