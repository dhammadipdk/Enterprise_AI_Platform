from enterprise_ai_platform.knowledge_engine import Chunk
from enterprise_ai_platform.knowledge_engine.indexing import BM25KeywordIndex


def _chunk(
    content: str,
    domain: str = "policy",
    asset: str = "glossary",
    chunk_index: int = 0,
) -> Chunk:

    return Chunk(
        content=content,
        repository="insurance",
        domain=domain,
        asset=asset,
        chunk_index=chunk_index,
    )


def test_empty_index_returns_no_results() -> None:

    index = BM25KeywordIndex()

    assert index.count() == 0

    assert index.search("insurance", "IDV") == []


def test_add_and_count() -> None:

    index = BM25KeywordIndex()

    index.add([_chunk("IDV means Insured Declared Value")])

    assert index.count() == 1


def test_search_finds_exact_term_match() -> None:

    index = BM25KeywordIndex()

    index.add(
        [
            _chunk("IDV means Insured Declared Value", chunk_index=0),
            _chunk("NCB means No Claim Bonus", chunk_index=1),
        ]
    )

    results = index.search("insurance", "IDV")

    assert len(results) == 1

    assert "IDV" in results[0].chunk.content


def test_search_scoped_to_domain() -> None:

    index = BM25KeywordIndex()

    index.add(
        [
            _chunk("IDV in policy domain", domain="policy", chunk_index=0),
            _chunk("IDV in claims domain", domain="claims", chunk_index=0),
        ]
    )

    results = index.search("insurance", "IDV", domain="claims")

    assert len(results) == 1

    assert results[0].chunk.domain == "claims"


def test_search_respects_top_k() -> None:

    index = BM25KeywordIndex()

    index.add(
        [
            _chunk("IDV term one", chunk_index=0),
            _chunk("IDV term two", chunk_index=1),
            _chunk("IDV term three", chunk_index=2),
        ]
    )

    results = index.search("insurance", "IDV", top_k=2)

    assert len(results) == 2


def test_search_no_match_returns_empty() -> None:

    index = BM25KeywordIndex()

    index.add([_chunk("something about claims and coverage")])

    assert index.search("insurance", "zzzznotpresent") == []


def test_upsert_replaces_existing_chunk() -> None:

    index = BM25KeywordIndex()

    index.add([_chunk("original content about IDV", chunk_index=0)])

    index.add([_chunk("updated content about NCB", chunk_index=0)])

    assert index.count() == 1

    results = index.search("insurance", "NCB")

    assert len(results) == 1

    assert "updated" in results[0].chunk.content


def test_clear_removes_all_chunks() -> None:

    index = BM25KeywordIndex()

    index.add([_chunk("IDV content")])

    index.clear()

    assert index.count() == 0