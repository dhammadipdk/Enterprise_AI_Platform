"""
Dataset loader.
"""

from pathlib import Path

from enterprise_ai_platform.dataset.dataset_registry import DatasetRegistry
from enterprise_ai_platform.dataset.models import Dataset
from enterprise_ai_platform.dataset.providers import (
    CSVDatasetProvider,
)


class DatasetLoader:
    """
    Loads datasets into the platform.
    """

    def __init__(
        self,
        registry: DatasetRegistry,
    ) -> None:

        self._registry = registry

        self._provider = CSVDatasetProvider()

    def load_csv(
        self,
        name: str,
        path: Path,
    ) -> None:

        records = self._provider.load(path)

        dataset = Dataset(
            name=name,
            records=records,
        )

        self._registry.register(
            name,
            dataset,
        )