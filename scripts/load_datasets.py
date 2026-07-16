"""
Load all datasets from the knowledge directory.
"""

from pathlib import Path

from enterprise_ai_platform.dataset import (
    DatasetLoader,
    DatasetRegistry,
)


def main() -> None:

    project_root = Path(__file__).resolve().parent.parent

    knowledge_directory = project_root / "knowledge"

    registry = DatasetRegistry()

    loader = DatasetLoader(registry)

    print("=" * 60)
    print("Enterprise AI Platform")
    print("Dataset Loader")
    print("=" * 60)
    print()

    print(f"Knowledge Directory : {knowledge_directory}")
    print()

    loader.load_directory(knowledge_directory)

    print("Loaded datasets")
    print("-" * 60)

    for dataset_name in registry.names():

        dataset = registry.get(dataset_name)

        print(
            f"✓ {dataset.name:<35}"
            f"{len(dataset.records):>8} records"
        )

    print("-" * 60)

    print(
        f"Total datasets : {len(registry.names())}"
    )


if __name__ == "__main__":
    main()