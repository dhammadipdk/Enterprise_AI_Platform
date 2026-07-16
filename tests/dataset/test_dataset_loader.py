from pathlib import Path

from enterprise_ai_platform.dataset import (
    DatasetLoader,
    DatasetRegistry,
)


def test_dataset_loader(tmp_path: Path) -> None:

    csv_file = tmp_path / "sample.csv"

    csv_file.write_text(
        "id,name\n"
        "1,Alice\n"
        "2,Bob\n"
    )

    registry = DatasetRegistry()

    loader = DatasetLoader(registry)

    loader.load_csv(
        "people",
        csv_file,
    )

    assert registry.exists("people")

    dataset = registry.get("people")

    assert dataset.name == "people"

    assert len(dataset.records) == 2

    assert dataset.records[0]["name"] == "Alice"