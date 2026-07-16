"""
Metadata loader.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from enterprise_ai_platform.metadata.metadata_registry import MetadataRegistry
from enterprise_ai_platform.metadata.models import MetadataRecord
from enterprise_ai_platform.metadata.providers import CSVProvider


class MetadataLoader:
    """
    Loads metadata into the platform registry.
    """

    def __init__(
        self,
        registry: MetadataRegistry,
    ) -> None:

        self._registry = registry

        self._provider = CSVProvider()

    def load_csv(
        self,
        name: str,
        path: Path,
    ) -> None:
        """
        Load one metadata CSV.
        """

        rows = self._provider.load(path)

        record = MetadataRecord(
            name=name,
            source=str(path),
            data={
                "rows": rows,
            },
        )

        self._registry.register(
            name,
            record,
        )