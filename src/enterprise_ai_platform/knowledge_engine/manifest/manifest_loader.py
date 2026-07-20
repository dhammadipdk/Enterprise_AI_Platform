"""
Knowledge manifest loader.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from enterprise_ai_platform.knowledge_engine.models import KnowledgeManifest


class ManifestLoader:
    """
    Loads an optional manifest.yaml from a domain directory.
    """

    MANIFEST_FILENAME = "manifest.yaml"

    def load(self, domain_directory: Path) -> KnowledgeManifest | None:
        """
        Load the manifest for a domain, if one exists.

        Returns None if no manifest file is present.
        """

        manifest_path = domain_directory / self.MANIFEST_FILENAME

        if not manifest_path.is_file():
            return None

        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

        if raw is None:
            raw = {}

        return KnowledgeManifest(**raw)