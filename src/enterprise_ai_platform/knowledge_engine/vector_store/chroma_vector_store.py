"""
Chroma vector store.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from enterprise_ai_platform.knowledge_engine.models import Chunk, EmbeddedChunk
from enterprise_ai_platform.knowledge_engine.vector_store.base_vector_store import (
    BaseVectorStore,
)
from enterprise_ai_platform.knowledge_engine.vector_store.vector_store_match import (
    VectorStoreMatch,
)

_SCALAR_TYPES = (str, int, float, bool)


class ChromaVectorStore(BaseVectorStore):
    """
    Vector store backed by ChromaDB, running fully in-process.

    By default this store is ephemeral (in-memory only, nothing written
    to disk) -- fast and isolated, ideal for tests and quick iteration.
    Pass a persist_directory to persist the index across process
    restarts.

    Chroma's default in-memory client shares its underlying System
    across every chromadb.Client() call within the same process (a
    documented Chroma quirk, not something this code controls). A fixed
    collection name would therefore leak data between unrelated
    ChromaVectorStore instances -- e.g. across tests, or across
    unrelated KnowledgeService instances. To guarantee isolation,
    ephemeral stores get a unique collection name per instance.
    Persistent stores keep the fixed name, since re-opening the same
    persist_directory is meant to surface the same data again.

    All chunks live in a single collection; repository/domain/asset are
    stored as filterable metadata rather than split across collections,
    keeping this simple for V1. Per-repository collections can be
    introduced later if true multi-tenant isolation is ever needed.
    """

    COLLECTION_NAME = "knowledge"

    def __init__(self, persist_directory: Path | str | None = None) -> None:

        self._persist_directory = (
            str(persist_directory) if persist_directory else None
        )

        self._client = None

        self._collection = None

        if self._persist_directory:
            self._collection_name = self.COLLECTION_NAME
        else:
            self._collection_name = (
                f"{self.COLLECTION_NAME}_{uuid.uuid4().hex}"
            )

    def _get_collection(self):
        """
        Lazily construct the Chroma client and collection.
        """

        if self._collection is None:

            import chromadb

            if self._persist_directory:
                self._client = chromadb.PersistentClient(
                    path=self._persist_directory
                )
            else:
                self._client = chromadb.Client()

            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )

        return self._collection

    def add(self, embedded_chunks: list[EmbeddedChunk]) -> None:
        """
        Add or update embedded chunks in the store.

        Uses upsert semantics keyed by a stable id derived from
        repository/domain/asset/chunk_index, so re-indexing the same
        asset replaces its previous chunks rather than duplicating them.
        """

        if not embedded_chunks:
            return

        collection = self._get_collection()

        ids = [self._chunk_id(item.chunk) for item in embedded_chunks]

        embeddings = [item.vector for item in embedded_chunks]

        documents = [item.chunk.content for item in embedded_chunks]

        metadatas = [
            self._build_metadata(item.chunk) for item in embedded_chunks
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorStoreMatch]:
        """
        Return the top_k most similar chunks to vector.

        filters uses Chroma metadata filter syntax, for example a
        single domain filter or an $and combination of repository and
        domain filters.
        """

        collection = self._get_collection()

        count = collection.count()

        if count == 0:
            return []

        results = collection.query(
            query_embeddings=[vector],
            n_results=min(top_k, count),
            where=filters,
            include=["documents", "metadatas", "distances"],
        )

        matches: list[VectorStoreMatch] = []

        documents = results["documents"][0]

        metadatas = results["metadatas"][0]

        distances = results["distances"][0]

        for document, metadata, distance in zip(
            documents, metadatas, distances
        ):

            chunk = Chunk(
                content=document,
                repository=metadata["repository"],
                domain=metadata["domain"],
                asset=metadata["asset"],
                chunk_index=metadata["chunk_index"],
                metadata=self._extract_chunk_metadata(metadata),
            )

            matches.append(
                VectorStoreMatch(
                    chunk=chunk,
                    score=1.0 - distance,
                )
            )

        return matches

    def count(self) -> int:
        """
        Return the number of chunks currently stored.
        """

        return self._get_collection().count()

    def clear(self) -> None:
        """
        Remove all chunks from the store.
        """

        collection = self._get_collection()

        existing = collection.get()

        if existing["ids"]:
            collection.delete(ids=existing["ids"])

    @staticmethod
    def _chunk_id(chunk: Chunk) -> str:

        return (
            f"{chunk.repository}:{chunk.domain}:"
            f"{chunk.asset}:{chunk.chunk_index}"
        )

    @classmethod
    def _build_metadata(cls, chunk: Chunk) -> dict[str, Any]:

        metadata: dict[str, Any] = {
            "repository": chunk.repository,
            "domain": chunk.domain,
            "asset": chunk.asset,
            "chunk_index": chunk.chunk_index,
        }

        for key, value in chunk.metadata.items():

            if isinstance(value, _SCALAR_TYPES):
                metadata[f"meta_{key}"] = value

        return metadata

    @staticmethod
    def _extract_chunk_metadata(metadata: dict[str, Any]) -> dict[str, Any]:

        return {
            key[len("meta_"):]: value
            for key, value in metadata.items()
            if key.startswith("meta_")
        }