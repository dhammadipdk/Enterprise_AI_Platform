from pathlib import Path

from enterprise_ai_platform.metadata import CSVProvider


def test_csv_provider_load(tmp_path: Path) -> None:

    csv_file = tmp_path / "sample.csv"

    csv_file.write_text(
        "name,age\n"
        "Alice,25\n"
        "Bob,30\n"
    )

    provider = CSVProvider()

    records = provider.load(csv_file)

    assert len(records) == 2

    assert records[0]["name"] == "Alice"

    assert records[1]["age"] == 30