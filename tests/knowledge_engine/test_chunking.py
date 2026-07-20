import pytest

from enterprise_ai_platform.knowledge_engine import (
    ChunkingStrategyRegistry,
    TabularChunker,
    TextChunker,
)


def test_text_chunker_single_chunk_for_short_content() -> None:

    chunker = TextChunker(chunk_size=500, chunk_overlap=50)

    chunks = chunker.chunk(
        "Zero depreciation cover.",
        repository="insurance",
        domain="policy",
        asset="README",
    )

    assert len(chunks) == 1

    assert chunks[0].content == "Zero depreciation cover."

    assert chunks[0].chunk_index == 0

    assert chunks[0].repository == "insurance"

    assert chunks[0].domain == "policy"

    assert chunks[0].asset == "README"


def test_text_chunker_splits_long_content_with_overlap() -> None:

    chunker = TextChunker(chunk_size=100, chunk_overlap=20)

    content = "a" * 250

    chunks = chunker.chunk(
        content,
        repository="insurance",
        domain="policy",
        asset="README",
    )

    assert len(chunks) == 3

    assert chunks[0].content == "a" * 100

    assert chunks[-1].metadata["end_offset"] == 250

    assert (
        chunks[0].metadata["end_offset"]
        - chunks[1].metadata["start_offset"]
        == 20
    )


def test_text_chunker_empty_content_returns_no_chunks() -> None:

    chunker = TextChunker()

    assert chunker.chunk("", "insurance", "policy", "README") == []


def test_text_chunker_rejects_overlap_greater_than_or_equal_to_size() -> None:

    with pytest.raises(ValueError):
        TextChunker(chunk_size=100, chunk_overlap=100)


def test_tabular_chunker_one_chunk_per_row() -> None:

    chunker = TabularChunker()

    rows = [
        {"term": "IDV", "definition": "Insured Declared Value"},
        {"term": "NCB", "definition": "No Claim Bonus"},
    ]

    chunks = chunker.chunk(
        rows,
        repository="insurance",
        domain="policy",
        asset="glossary",
    )

    assert len(chunks) == 2

    assert (
        chunks[0].content == "term: IDV\ndefinition: Insured Declared Value"
    )

    assert chunks[0].metadata == rows[0]

    assert chunks[1].chunk_index == 1


def test_tabular_chunker_empty_rows_returns_no_chunks() -> None:

    chunker = TabularChunker()

    assert chunker.chunk([], "insurance", "policy", "glossary") == []


def test_chunking_strategy_registry_dispatch() -> None:

    registry = ChunkingStrategyRegistry()

    registry.register(".md", TextChunker())

    strategy = registry.get(".md")

    chunks = strategy.chunk("hello world", "insurance", "policy", "README")

    assert len(chunks) == 1