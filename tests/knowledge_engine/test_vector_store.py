from enterprise_ai_platform.knowledge_engine import Chunk, EmbeddedChunk
from enterprise_ai_platform.knowledge_engine.vector_store import (
    ChromaVectorStore,
)


def _embedded_chunk(
    content: str,
    vector: list[float],
    repository: str = "insurance",
    domain: str = "policy",
    asset: str = "glossary",
    chunk_index: int = 0,
    metadata: dict | None = None,
) -> EmbeddedChunk:

    return EmbeddedChunk(
        chunk=Chunk(
            content=content,
            repository=repository,
            domain=domain,
            asset=asset,
            chunk_index=chunk_index,
            metadata=metadata or {},
        ),
        vector=vector,
        provider="fake",
    )


def test_empty_store_has_zero_count() -> None:

    store = ChromaVectorStore()

    assert store.count() == 0


def test_add_and_count() -> None:

    store = ChromaVectorStore()

    store.add(
        [
            _embedded_chunk("IDV means Insured Declared Value", [1.0, 0.0]),
            _embedded_chunk(
                "NCB means No Claim Bonus", [0.0, 1.0], chunk_index=1
            ),
        ]
    )

    assert store.count() == 2


def test_add_empty_list_is_a_no_op() -> None:

    store = ChromaVectorStore()

    store.add([])

    assert store.count() == 0


def test_query_returns_closest_match_first() -> None:

    store = ChromaVectorStore()

    store.add(
        [
            _embedded_chunk("about IDV", [1.0, 0.0], chunk_index=0),
            _embedded_chunk("about NCB", [0.0, 1.0], chunk_index=1),
        ]
    )

    results = store.query([0.9, 0.1], top_k=1)

    assert len(results) == 1

    assert results[0].chunk.content == "about IDV"

    assert results[0].score > 0.5


def test_query_respects_top_k() -> None:

    store = ChromaVectorStore()

    store.add(
        [
            _embedded_chunk("a", [1.0, 0.0], chunk_index=0),
            _embedded_chunk("b", [0.0, 1.0], chunk_index=1),
        ]
    )

    results = store.query([1.0, 0.0], top_k=1)

    assert len(results) == 1


def test_query_top_k_larger_than_store_size_returns_all() -> None:

    store = ChromaVectorStore()

    store.add([_embedded_chunk("only one", [1.0, 0.0])])

    results = store.query([1.0, 0.0], top_k=10)

    assert len(results) == 1


def test_query_on_empty_store_returns_empty_list() -> None:

    store = ChromaVectorStore()

    assert store.query([1.0, 0.0]) == []


def test_query_filters_by_metadata() -> None:

    store = ChromaVectorStore()

    store.add(
        [
            _embedded_chunk(
                "policy chunk",
                [1.0, 0.0],
                domain="policy",
                chunk_index=0,
            ),
            _embedded_chunk(
                "claims chunk",
                [1.0, 0.0],
                domain="claims",
                chunk_index=1,
            ),
        ]
    )

    results = store.query(
        [1.0, 0.0], top_k=5, filters={"domain": "claims"}
    )

    assert len(results) == 1

    assert results[0].chunk.content == "claims chunk"


def test_upsert_replaces_existing_chunk() -> None:

    store = ChromaVectorStore()

    store.add([_embedded_chunk("original", [1.0, 0.0], chunk_index=0)])

    store.add([_embedded_chunk("updated", [1.0, 0.0], chunk_index=0)])

    assert store.count() == 1

    results = store.query([1.0, 0.0], top_k=1)

    assert results[0].chunk.content == "updated"


def test_clear_removes_all_chunks() -> None:

    store = ChromaVectorStore()

    store.add([_embedded_chunk("something", [1.0, 0.0])])

    store.clear()

    assert store.count() == 0


def test_scalar_metadata_round_trips() -> None:

    store = ChromaVectorStore()

    store.add(
        [
            _embedded_chunk(
                "term row",
                [1.0, 0.0],
                metadata={"term": "IDV", "year": 2024},
            )
        ]
    )

    results = store.query([1.0, 0.0], top_k=1)

    assert results[0].chunk.metadata == {"term": "IDV", "year": 2024}