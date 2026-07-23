"""
BM25 keyword index.
"""

from __future__ import annotations

import re

from enterprise_ai_platform.knowledge_engine.indexing.base_keyword_index import (
    BaseKeywordIndex,
)
from enterprise_ai_platform.knowledge_engine.models import Chunk
from enterprise_ai_platform.knowledge_engine.vector_store import VectorStoreMatch


class BM25KeywordIndex(BaseKeywordIndex):
    """
    In-process lexical (keyword) search over chunk content, using BM25.

    This is the "sparse" / exact-term half of hybrid retrieval -- it
    excels at exact terms, codes and clause numbers that dense
    embeddings can blur together (e.g. "Section 64VB", an IRDAI
    circular number, a specific insurer name). Runs fully in-process
    via the rank_bm25 package, no external service, no cost.

    Chunks are held in memory and re-ranked per query against the
    filtered candidate set (repository / domain), rather than
    maintaining one persistent BM25 index per repository. At V1 scale
    (low thousands of chunks) this keeps the implementation simple
    with no measurable performance cost.

    A chunk is only ever returned if it shares at least one token with
    the query. Classic BM25's IDF term can be zero or negative for a
    word that appears in most/all documents of a small corpus -- an
    expected situation while these knowledge domains are still small
    -- so relevance is gated on actual token overlap, and the BM25
    score is used only to rank among chunks that already passed that
    gate, never to decide inclusion.
    """

    def __init__(self) -> None:

        self._chunks: list[Chunk] = []

    def add(self, chunks: list[Chunk]) -> None:
        """
        Add chunks to the index.

        Uses upsert semantics: a chunk sharing the same
        repository/domain/asset/chunk_index as an existing entry
        replaces it, mirroring ChromaVectorStore's upsert behavior.
        """

        for chunk in chunks:

            self._chunks = [
                existing
                for existing in self._chunks
                if self._chunk_id(existing) != self._chunk_id(chunk)
            ]

            self._chunks.append(chunk)

    def search(
        self,
        repository: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[VectorStoreMatch]:
        """
        Return the top_k chunks most relevant to query_text by BM25
        score, scoped to repository (and optionally domain).

        Only chunks sharing at least one token with the query are
        returned; BM25 score is used purely to rank among those.
        """

        candidates = [
            chunk
            for chunk in self._chunks
            if chunk.repository == repository
            and (domain is None or chunk.domain == domain)
        ]

        if not candidates:
            return []

        query_tokens = self._tokenize(query_text)

        if not query_tokens:
            return []

        query_token_set = set(query_tokens)

        tokenized_corpus = [
            self._tokenize(chunk.content) for chunk in candidates
        ]

        matching_indices = [
            index
            for index, tokens in enumerate(tokenized_corpus)
            if query_token_set & set(tokens)
        ]

        if not matching_indices:
            return []

        from rank_bm25 import BM25Okapi

        bm25 = BM25Okapi(tokenized_corpus)

        scores = bm25.get_scores(query_tokens)

        ranked = sorted(
            (
                (candidates[index], scores[index])
                for index in matching_indices
            ),
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            VectorStoreMatch(chunk=chunk, score=float(score))
            for chunk, score in ranked[:top_k]
        ]

    def count(self) -> int:
        """
        Return the number of chunks currently indexed.
        """

        return len(self._chunks)

    def clear(self) -> None:
        """
        Remove all chunks from the index.
        """

        self._chunks = []

    @staticmethod
    def _tokenize(text: str) -> list[str]:

        return re.findall(r"[a-z0-9]+", text.lower())

    @staticmethod
    def _chunk_id(chunk: Chunk) -> str:

        return (
            f"{chunk.repository}:{chunk.domain}:"
            f"{chunk.asset}:{chunk.chunk_index}"
        )