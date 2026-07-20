"""
Knowledge repository loader.
"""

from pathlib import Path

from enterprise_ai_platform.knowledge_engine.models import (
    KnowledgeAsset,
    KnowledgeDomain,
    KnowledgeRepository,
)


class KnowledgeRepositoryLoader:
    """
    Builds a KnowledgeRepository from the filesystem.
    """

    def load(
        self,
        knowledge_root: Path,
    ) -> KnowledgeRepository:

        domains: list[KnowledgeDomain] = []

        for directory in sorted(knowledge_root.iterdir()):

            if not directory.is_dir():
                continue

            assets: list[KnowledgeAsset] = []

            for file in sorted(directory.rglob("*")):

                if not file.is_file():
                    continue

                relative = file.relative_to(directory)

                asset = KnowledgeAsset(
                    name=relative.stem,
                    asset_type=self._infer_asset_type(relative),
                    path=file,
                )

                assets.append(asset)

            domains.append(
                KnowledgeDomain(
                    name=directory.name,
                    assets=assets,
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