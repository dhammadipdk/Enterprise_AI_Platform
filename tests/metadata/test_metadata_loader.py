from pathlib import Path

from enterprise_ai_platform.metadata import (
    MetadataLoader,
    MetadataRegistry,
)


def test_metadata_loader(tmp_path: Path) -> None:

    csv_file = tmp_path / "people.csv"

    csv_file.write_text(
        "name,age\n"
        "Alice,25\n"
        "Bob,30\n"
    )

    registry = MetadataRegistry()

    loader = MetadataLoader(registry)

    loader.load_csv(
        "people",
        csv_file,
    )

    assert registry.exists("people")

    record = registry.get("people")

    assert record.name == "people"

    assert len(record.data["rows"]) == 2

    assert record.data["rows"][0]["name"] == "Alice"