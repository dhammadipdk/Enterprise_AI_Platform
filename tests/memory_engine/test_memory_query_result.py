from enterprise_ai_platform.memory_engine import (
    MemoryItem,
    MemoryQuery,
    MemoryResult,
    MemoryType,
)


def test_query_defaults() -> None:

    query = MemoryQuery()

    assert query.collection is None

    assert query.include_expired is False

    assert query.limit == 10


def test_result_score_defaults_to_none() -> None:

    item = MemoryItem(
        memory_type=MemoryType.EPISODIC, content="a", collection="c1"
    )

    result = MemoryResult(item=item)

    assert result.score is None