"""
Knowledge service.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from enterprise_ai_platform.framework.base import (
    BaseProvider,
    BaseService,
    ComponentState,
)
from enterprise_ai_platform.knowledge_engine.chunking import (
    BaseChunkingStrategy,
    ChunkingStrategyRegistry,
    TabularChunker,
    TextChunker,
)
from enterprise_ai_platform.knowledge_engine.embedding import (
    BaseEmbeddingProvider,
    EmbeddingPipeline,
    LocalEmbeddingProvider,
)
from enterprise_ai_platform.knowledge_engine.indexing import (
    BaseKeywordIndex,
    BM25KeywordIndex,
)
from enterprise_ai_platform.knowledge_engine.loaders import (
    KnowledgeRepositoryLoader,
)
from enterprise_ai_platform.knowledge_engine.models import (
    Chunk,
    EmbeddedChunk,
    KnowledgeAsset,
    KnowledgeDomain,
    KnowledgeManifest,
    KnowledgeRepository,
)
from enterprise_ai_platform.knowledge_engine.providers import (
    CSVProvider,
    KnowledgeProviderRegistry,
    MarkdownProvider,
)
from enterprise_ai_platform.knowledge_engine.registry.knowledge_registry import (
    KnowledgeRegistry,
)
from enterprise_ai_platform.knowledge_engine.retrieval import (
    HybridRetriever,
    Retriever,
)
from enterprise_ai_platform.knowledge_engine.validation import (
    RepositoryValidator,
    ValidationReport,
)
from enterprise_ai_platform.knowledge_engine.vector_store import (
    BaseVectorStore,
    ChromaVectorStore,
    VectorStoreMatch,
)


class KnowledgeService(BaseService):
    """
    Public API of the Knowledge Engine.

    Every other subsystem interacts with knowledge exclusively through
    this service. Nothing outside the Knowledge Engine should reference
    KnowledgeRepositoryLoader, KnowledgeRegistry, KnowledgeRepository,
    the providers, chunking strategies, embedding provider, vector
    store, keyword index or retrievers directly.
    """

    def __init__(self) -> None:

        super().__init__(name="knowledge_service")

        self._registry = KnowledgeRegistry()

        self._loader = KnowledgeRepositoryLoader()

        self._providers = KnowledgeProviderRegistry()

        self._providers.register(".csv", CSVProvider())

        self._providers.register(".md", MarkdownProvider())

        self._validator = RepositoryValidator()

        self._chunkers = ChunkingStrategyRegistry()

        self._chunkers.register(".csv", TabularChunker())

        self._chunkers.register(".md", TextChunker())

        self._embedding_pipeline = EmbeddingPipeline(LocalEmbeddingProvider())

        self._vector_store: BaseVectorStore = ChromaVectorStore()

        self._keyword_index: BaseKeywordIndex = BM25KeywordIndex()

        self._retriever = Retriever(self.search)

        self._hybrid_retriever = HybridRetriever(
            self.search,
            self.keyword_search,
        )

    def initialize(self) -> None:
        """
        Initialize the service.
        """

        self._set_state(ComponentState.INITIALIZED)

    def start(self) -> None:
        """
        Start the service.
        """

        self._set_state(ComponentState.RUNNING)

    def stop(self) -> None:
        """
        Stop the service.
        """

        self._set_state(ComponentState.STOPPED)

    def dispose(self) -> None:
        """
        Dispose the service and clear all loaded repositories.
        """

        self._registry.clear()

        self._set_state(ComponentState.DISPOSED)

    # ------------------------------------------------------------------
    # Repository management
    # ------------------------------------------------------------------

    def load_repository(
        self,
        name: str,
        knowledge_root: Path,
    ) -> KnowledgeRepository:
        """
        Load a knowledge repository from disk and register it under `name`.
        """

        repository = self._loader.load(knowledge_root)

        self._registry.register(name, repository)

        return repository

    def reload_repository(
        self,
        name: str,
        knowledge_root: Path,
    ) -> KnowledgeRepository:
        """
        Reload a repository from disk, replacing whatever is currently
        registered under `name`.
        """

        repository = self._loader.load(knowledge_root)

        if self._registry.exists(name):
            self._registry.unregister(name)

        self._registry.register(name, repository)

        return repository

    def get_repository(self, name: str) -> KnowledgeRepository:
        """
        Return a registered repository.
        """

        return self._registry.get(name)

    def repository_exists(self, name: str) -> bool:
        """
        Return True if a repository is registered under `name`.
        """

        return self._registry.exists(name)

    def list_repositories(self) -> list[str]:
        """
        Return the names of every registered repository.
        """

        return self._registry.names()

    # ------------------------------------------------------------------
    # Domain access
    # ------------------------------------------------------------------

    def list_domains(self, name: str) -> list[str]:
        """
        Return the domain names within a repository.
        """

        repository = self.get_repository(name)

        return [domain.name for domain in repository.domains]

    def get_domain(self, name: str, domain: str) -> KnowledgeDomain:
        """
        Return a single domain from a repository.
        """

        repository = self.get_repository(name)

        for candidate in repository.domains:

            if candidate.name == domain:
                return candidate

        raise KeyError(
            f"No domain named '{domain}' in repository '{name}'."
        )

    def get_manifest(
        self,
        name: str,
        domain: str,
    ) -> KnowledgeManifest | None:
        """
        Return the manifest for a domain, if one exists.
        """

        return self.get_domain(name, domain).manifest

    # ------------------------------------------------------------------
    # Asset access
    # ------------------------------------------------------------------

    def list_assets(self, name: str, domain: str) -> list[str]:
        """
        Return the asset names within a domain.
        """

        return [
            asset.name
            for asset in self.get_domain(name, domain).assets
        ]

    def get_asset(
        self,
        name: str,
        domain: str,
        asset: str,
    ) -> KnowledgeAsset:
        """
        Return a single asset from a domain.
        """

        target_domain = self.get_domain(name, domain)

        for candidate in target_domain.assets:

            if candidate.name == asset:
                return candidate

        raise KeyError(
            f"No asset named '{asset}' in domain '{domain}' "
            f"of repository '{name}'."
        )

    # ------------------------------------------------------------------
    # Providers / content loading
    # ------------------------------------------------------------------

    def register_provider(
        self,
        extension: str,
        provider: BaseProvider,
    ) -> None:
        """
        Register a provider for a file extension, e.g. ".json", ".pdf".

        Overwrites any provider already registered for that extension.
        """

        if self._providers.exists(extension):
            self._providers.unregister(extension)

        self._providers.register(extension, provider)

    def load_asset_content(
        self,
        name: str,
        domain: str,
        asset: str,
    ) -> Any:
        """
        Load the actual content of an asset using the matching provider,
        dispatched by file extension.
        """

        target_asset = self.get_asset(name, domain, asset)

        extension = target_asset.path.suffix.lower()

        if not self._providers.exists(extension):
            raise ValueError(
                f"No knowledge provider registered for extension "
                f"'{extension}' (asset '{asset}' in domain '{domain}' "
                f"of repository '{name}')."
            )

        provider = self._providers.get(extension)

        return provider.load(target_asset.path)

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def register_chunking_strategy(
        self,
        extension: str,
        strategy: BaseChunkingStrategy,
    ) -> None:
        """
        Register a chunking strategy for a file extension, e.g. ".json".

        Overwrites any strategy already registered for that extension.
        """

        if self._chunkers.exists(extension):
            self._chunkers.unregister(extension)

        self._chunkers.register(extension, strategy)

    def chunk_asset(
        self,
        name: str,
        domain: str,
        asset: str,
    ) -> list[Chunk]:
        """
        Load and chunk an asset's content using the matching strategy,
        dispatched by file extension.
        """

        target_asset = self.get_asset(name, domain, asset)

        extension = target_asset.path.suffix.lower()

        if not self._chunkers.exists(extension):
            raise ValueError(
                f"No chunking strategy registered for extension "
                f"'{extension}' (asset '{asset}' in domain '{domain}' "
                f"of repository '{name}')."
            )

        content = self.load_asset_content(name, domain, asset)

        strategy = self._chunkers.get(extension)

        return strategy.chunk(content, name, domain, asset)

    def chunk_domain(
        self,
        name: str,
        domain: str,
    ) -> list[Chunk]:
        """
        Chunk every asset in a domain.

        Assets whose extension has no registered chunking strategy are
        silently skipped.
        """

        chunks: list[Chunk] = []

        for asset_name in self.list_assets(name, domain):

            asset = self.get_asset(name, domain, asset_name)

            extension = asset.path.suffix.lower()

            if not self._chunkers.exists(extension):
                continue

            chunks.extend(self.chunk_asset(name, domain, asset_name))

        return chunks

    def chunk_repository(
        self,
        name: str,
    ) -> list[Chunk]:
        """
        Chunk every asset across every domain in a repository.
        """

        chunks: list[Chunk] = []

        for domain in self.list_domains(name):
            chunks.extend(self.chunk_domain(name, domain))

        return chunks

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def set_embedding_provider(self, provider: BaseEmbeddingProvider) -> None:
        """
        Swap the active embedding provider (e.g. local -> API-based)
        without changing any other Knowledge Engine code.
        """

        self._embedding_pipeline = EmbeddingPipeline(provider)

    def get_embedding_provider(self) -> BaseEmbeddingProvider:
        """
        Return the currently active embedding provider.
        """

        return self._embedding_pipeline.provider

    def embed_asset(
        self,
        name: str,
        domain: str,
        asset: str,
    ) -> list[EmbeddedChunk]:
        """
        Chunk and embed a single asset.
        """

        chunks = self.chunk_asset(name, domain, asset)

        return self._embedding_pipeline.embed(chunks)

    def embed_domain(
        self,
        name: str,
        domain: str,
    ) -> list[EmbeddedChunk]:
        """
        Chunk and embed every asset in a domain.
        """

        chunks = self.chunk_domain(name, domain)

        return self._embedding_pipeline.embed(chunks)

    def embed_repository(
        self,
        name: str,
    ) -> list[EmbeddedChunk]:
        """
        Chunk and embed every asset across every domain in a repository.
        """

        chunks = self.chunk_repository(name)

        return self._embedding_pipeline.embed(chunks)

    # ------------------------------------------------------------------
    # Vector store / search
    # ------------------------------------------------------------------

    def set_vector_store(self, store: BaseVectorStore) -> None:
        """
        Swap the active vector store (e.g. in-memory -> persistent, or
        Chroma -> another backend) without changing any other Knowledge
        Engine code.
        """

        self._vector_store = store

    def get_vector_store(self) -> BaseVectorStore:
        """
        Return the currently active vector store.
        """

        return self._vector_store

    def index_asset(self, name: str, domain: str, asset: str) -> int:
        """
        Embed a single asset and add its chunks to the vector store
        and the keyword index.

        Returns the number of chunks indexed.
        """

        embedded = self.embed_asset(name, domain, asset)

        self._vector_store.add(embedded)

        self._keyword_index.add([item.chunk for item in embedded])

        return len(embedded)

    def index_domain(self, name: str, domain: str) -> int:
        """
        Embed every asset in a domain and add the chunks to the vector
        store and the keyword index.
        """

        embedded = self.embed_domain(name, domain)

        self._vector_store.add(embedded)

        self._keyword_index.add([item.chunk for item in embedded])

        return len(embedded)

    def index_repository(self, name: str) -> int:
        """
        Embed every asset across a repository and add the chunks to
        the vector store and the keyword index.
        """

        embedded = self.embed_repository(name)

        self._vector_store.add(embedded)

        self._keyword_index.add([item.chunk for item in embedded])

        return len(embedded)

    def search(
        self,
        name: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[VectorStoreMatch]:
        """
        Embed `query_text` and return the top_k most similar chunks
        from repository `name`, optionally narrowed to one domain.
        """

        vector = self._embedding_pipeline.provider.embed_text(query_text)

        conditions: list[dict[str, Any]] = [{"repository": name}]

        if domain is not None:
            conditions.append({"domain": domain})

        filters = (
            conditions[0] if len(conditions) == 1 else {"$and": conditions}
        )

        return self._vector_store.query(
            vector,
            top_k=top_k,
            filters=filters,
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        name: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[VectorStoreMatch]:
        """
        Return relevant chunks for a query, above the configured
        minimum relevance score.
        """

        return self._retriever.retrieve(
            name,
            query_text,
            top_k=top_k,
            domain=domain,
        )

    def retrieve_context(
        self,
        name: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> str:
        """
        Retrieve relevant chunks for a query and render them into a
        single text block ready to inject into a prompt.
        """

        return self._retriever.retrieve_as_context(
            name,
            query_text,
            top_k=top_k,
            domain=domain,
        )

    def set_retrieval_score_threshold(self, score_threshold: float) -> None:
        """
        Set the minimum relevance score a match must meet to be
        returned by retrieve() / retrieve_context().
        """

        self._retriever = Retriever(
            self.search,
            score_threshold=score_threshold,
        )

    def get_retrieval_score_threshold(self) -> float:
        """
        Return the currently configured minimum relevance score.
        """

        return self._retriever.score_threshold

    # ------------------------------------------------------------------
    # Keyword / hybrid search
    # ------------------------------------------------------------------

    def set_keyword_index(self, index: BaseKeywordIndex) -> None:
        """
        Swap the active keyword index without changing any other
        Knowledge Engine code.
        """

        self._keyword_index = index

    def get_keyword_index(self) -> BaseKeywordIndex:
        """
        Return the currently active keyword index.
        """

        return self._keyword_index

    def keyword_search(
        self,
        name: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[VectorStoreMatch]:
        """
        Return the top_k chunks most relevant to `query_text` by exact
        lexical (BM25) match, scoped to repository `name` and
        optionally one domain.
        """

        return self._keyword_index.search(
            name,
            query_text,
            top_k=top_k,
            domain=domain,
        )

    def hybrid_search(
        self,
        name: str,
        query_text: str,
        top_k: int = 5,
        domain: str | None = None,
        candidate_pool: int = 20,
    ) -> list[VectorStoreMatch]:
        """
        Return the top_k chunks by combining semantic (vector) search
        with keyword (BM25) search via Reciprocal Rank Fusion.
        """

        return self._hybrid_retriever.retrieve(
            name,
            query_text,
            top_k=top_k,
            domain=domain,
            candidate_pool=candidate_pool,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_repository(self, name: str) -> ValidationReport:
        """
        Validate a registered repository and return the report.
        """

        repository = self.get_repository(name)

        return self._validator.validate(repository)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def repository_statistics(self, name: str) -> dict:
        """
        Return summary statistics for a repository.
        """

        repository = self.get_repository(name)

        asset_type_counts: dict[str, int] = {}

        total_assets = 0

        for domain in repository.domains:

            for asset in domain.assets:

                total_assets += 1

                asset_type_counts[asset.asset_type] = (
                    asset_type_counts.get(asset.asset_type, 0) + 1
                )

        return {
            "domain_count": len(repository.domains),
            "asset_count": total_assets,
            "asset_types": asset_type_counts,
        }