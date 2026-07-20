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
from enterprise_ai_platform.knowledge_engine.loaders import (
    KnowledgeRepositoryLoader,
)
from enterprise_ai_platform.knowledge_engine.models import (
    Chunk,
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
from enterprise_ai_platform.knowledge_engine.validation import (
    RepositoryValidator,
    ValidationReport,
)


class KnowledgeService(BaseService):
    """
    Public API of the Knowledge Engine.

    Every other subsystem interacts with knowledge exclusively through
    this service. Nothing outside the Knowledge Engine should reference
    KnowledgeRepositoryLoader, KnowledgeRegistry, KnowledgeRepository or
    the providers / chunking strategies directly.
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