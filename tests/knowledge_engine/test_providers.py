from pathlib import Path

from enterprise_ai_platform.knowledge_engine import (
    CSVProvider,
    KnowledgeProviderRegistry,
    MarkdownProvider,
)


def test_csv_provider_load(tmp_path: Path) -> None:

    csv_file = tmp_path / "glossary.csv"

    csv_file.write_text(
        "term,definition\n"
        "IDV,Insured Declared Value\n"
        "NCB,No Claim Bonus\n"
    )

    provider = CSVProvider()

    records = provider.load(csv_file)

    assert len(records) == 2

    assert records[0]["term"] == "IDV"

    assert records[1]["definition"] == "No Claim Bonus"


def test_markdown_provider_load(tmp_path: Path) -> None:

    markdown_file = tmp_path / "README.md"

    markdown_file.write_text("# Policy Domain\n\nOverview text.")

    provider = MarkdownProvider()

    content = provider.load(markdown_file)

    assert content.startswith("# Policy Domain")


def test_provider_registry_dispatch(tmp_path: Path) -> None:

    csv_file = tmp_path / "sample.csv"

    csv_file.write_text("a,b\n1,2\n")

    registry = KnowledgeProviderRegistry()

    registry.register(".csv", CSVProvider())

    provider = registry.get(".csv")

    records = provider.load(csv_file)

    assert records[0]["a"] == 1