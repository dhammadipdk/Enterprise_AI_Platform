"""
Knowledge service.
"""

from __future__ import annotations

from pathlib import Path

from enterprise_ai_platform.framework.base import (
    BaseService,
    ComponentState,
)
from enterprise_ai_platform.knowledge_engine.loaders import (
    KnowledgeRepositoryLoader,
)
from enterprise_ai_platform.knowledge_engine.models import (
    KnowledgeAsset,
    KnowledgeDomain,
    KnowledgeRepository,
)
from enterprise_ai_platform.knowledge_engine.registry.knowledge_registry import (
    KnowledgeRegistry,
)


class KnowledgeService(BaseService):
    """
    Public API of the Knowledge Engine.

    Every other subsystem interacts with knowledge exclusively through
    this service. Nothing outside the Knowledge Engine should reference
    KnowledgeRepositoryLoader, KnowledgeRegistry or KnowledgeRepository
    directly.
    """

    def __init__(self) -> None:

        super().__init__(name="knowledge_service")

        self._registry = KnowledgeRegistry()

        self._loader = KnowledgeRepositoryLoader()

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