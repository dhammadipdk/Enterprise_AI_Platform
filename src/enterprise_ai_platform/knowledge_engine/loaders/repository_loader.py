"""
Knowledge repository loader.
"""

from __future__ import annotations

from pathlib import Path

from enterprise_ai_platform.knowledge_engine.manifest import ManifestLoader
from enterprise_ai_platform.knowledge_engine.models import (
    KnowledgeAsset,
    KnowledgeDomain,
    KnowledgeRepository,
)


class KnowledgeRepositoryLoader:
    """
    Builds a KnowledgeRepository from the filesystem.
    """

    def __init__(self) -> None:

        self._manifest_loader = ManifestLoader()

    def load(
        self,
        knowledge_root: Path,
    ) -> KnowledgeRepository:

        domains: list[KnowledgeDomain] = []

        for directory in sorted(knowledge_root.iterdir()):

            if not directory.is_dir():
                continue

            manifest = self._manifest_loader.load(directory)

            overrides = manifest.asset_type_overrides if manifest else {}

            assets: list[KnowledgeAsset] = []

            for file in sorted(directory.rglob("*")):

                if not file.is_file():
                    continue

                if file.name == ManifestLoader.MANIFEST_FILENAME:
                    continue

                relative = file.relative_to(directory)

                asset_name = relative.stem

                asset_type = overrides.get(
                    asset_name,
                    self._infer_asset_type(relative),
                )

                asset = KnowledgeAsset(
                    name=asset_name,
                    asset_type=asset_type,
                    path=file,
                )

                assets.append(asset)

            domains.append(
                KnowledgeDomain(
                    name=directory.name,
                    assets=assets,
                    manifest=manifest,
                )
            )

        return KnowledgeRepository(
            domains=domains,
        )

    @staticmethod
    def _infer_asset_type(path: Path) -> str:

        filename = path.stem.lower()

        mapping = {
            "canonical_schema": "schema",
            "entity_catalog": "catalog",
            "glossary": "glossary",
            "readme": "documentation",
            "seed_data": "seed_data",
            "relationships": "relationship",
        }

        return mapping.get(
            filename,
            "generic",
        )