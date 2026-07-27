from datetime import datetime, timedelta, timezone

import pytest

from enterprise_ai_platform.memory_engine import (
    MemoryQuery,
    MemoryService,
    MemoryType,
)


def test_store_and_retrieve() -> None:

    service = MemoryService()

    item = service.store(
        memory_type=MemoryType.EPISODIC,
        content="Customer asked about zero dep.",
        collection="conversation:s1",
        metadata={"topic": "zero_dep"},
        owner="user123",
    )

    retrieved = service.retrieve(item.memory_id)

    assert retrieved.content == "Customer asked about zero dep."

    assert retrieved.metadata["topic"] == "zero_dep"


def test_retrieve_missing_raises_key_error() -> None:

    service = MemoryService()

    with pytest.raises(KeyError):
        service.retrieve("does_not_exist")


def test_retrieve_expired_raises_key_error() -> None:

    service = MemoryService()

    item = service.store(
        memory_type=MemoryType.WORKING,
        content="temporary",
        collection="workflow:w1",
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )

    with pytest.raises(KeyError, match="expired"):
        service.retrieve(item.memory_id)


def test_search_filters_by_collection() -> None:

    service = MemoryService()

    service.store(
        memory_type=MemoryType.EPISODIC,
        content="s1 memory",
        collection="conversation:s1",
    )

    service.store(
        memory_type=MemoryType.EPISODIC,
        content="s2 memory",
        collection="conversation:s2",
    )

    results = service.search(MemoryQuery(collection="conversation:s1"))

    assert len(results) == 1

    assert results[0].item.content == "s1 memory"


def test_search_orders_most_recent_first() -> None:

    service = MemoryService()

    first = service.store(
        memory_type=MemoryType.EPISODIC,
        content="first",
        collection="conversation:s1",
    )

    second = service.store(
        memory_type=MemoryType.EPISODIC,
        content="second",
        collection="conversation:s1",
    )

    results = service.search(MemoryQuery(collection="conversation:s1"))

    assert [r.item.content for r in results] == ["second", "first"]


def test_search_filters_by_metadata() -> None:

    service = MemoryService()

    service.store(
        memory_type=MemoryType.EPISODIC,
        content="a",
        collection="conversation:s1",
        metadata={"topic": "zero_dep"},
    )

    service.store(
        memory_type=MemoryType.EPISODIC,
        content="b",
        collection="conversation:s1",
        metadata={"topic": "ncb"},
    )

    results = service.search(
        MemoryQuery(metadata_filter={"topic": "zero_dep"})
    )

    assert len(results) == 1

    assert results[0].item.content == "a"


def test_search_excludes_expired_by_default() -> None:

    service = MemoryService()

    service.store(
        memory_type=MemoryType.WORKING,
        content="expired",
        collection="workflow:w1",
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )

    assert service.search(MemoryQuery()) == []

    results = service.search(MemoryQuery(include_expired=True))

    assert len(results) == 1


def test_search_respects_limit() -> None:

    service = MemoryService()

    for i in range(5):
        service.store(
            memory_type=MemoryType.EPISODIC,
            content=f"item {i}",
            collection="conversation:s1",
        )

    results = service.search(MemoryQuery(limit=2))

    assert len(results) == 2


def test_list_collections() -> None:

    service = MemoryService()

    service.store(
        memory_type=MemoryType.EPISODIC, content="a", collection="conversation:s1"
    )

    service.store(
        memory_type=MemoryType.EPISODIC, content="b", collection="workflow:w1"
    )

    assert service.list_collections() == ["conversation:s1", "workflow:w1"]


def test_update_metadata_merges_and_increments_version() -> None:

    service = MemoryService()

    item = service.store(
        memory_type=MemoryType.EPISODIC,
        content="a",
        collection="conversation:s1",
        metadata={"topic": "zero_dep"},
    )

    updated = service.update_metadata(item.memory_id, {"resolved": True})

    assert updated.metadata == {"topic": "zero_dep", "resolved": True}

    assert updated.version == 2

    assert updated.content == "a"


def test_archive_excludes_from_search_but_not_retrieve() -> None:

    service = MemoryService()

    item = service.store(
        memory_type=MemoryType.EPISODIC, content="a", collection="conversation:s1"
    )

    service.archive(item.memory_id)

    assert service.is_archived(item.memory_id)

    assert service.search(MemoryQuery(collection="conversation:s1")) == []

    assert service.retrieve(item.memory_id).content == "a"


def test_delete_removes_permanently() -> None:

    service = MemoryService()

    item = service.store(
        memory_type=MemoryType.EPISODIC, content="a", collection="conversation:s1"
    )

    service.delete(item.memory_id)

    with pytest.raises(KeyError):
        service.retrieve(item.memory_id)


def test_delete_missing_raises_key_error() -> None:

    service = MemoryService()

    with pytest.raises(KeyError):
        service.delete("does_not_exist")


def test_statistics() -> None:

    service = MemoryService()

    service.store(
        memory_type=MemoryType.EPISODIC, content="a", collection="conversation:s1"
    )

    service.store(
        memory_type=MemoryType.SEMANTIC, content="b", collection="conversation:s1"
    )

    item = service.store(
        memory_type=MemoryType.EPISODIC, content="c", collection="conversation:s1"
    )

    service.archive(item.memory_id)

    stats = service.statistics()

    assert stats["total_items"] == 3

    assert stats["archived_items"] == 1

    assert stats["collections"] == 1

    assert stats["by_type"] == {"episodic": 2, "semantic": 1}


def test_health_is_true_for_in_memory_backend() -> None:

    service = MemoryService()

    assert service.health() is True


def test_lifecycle_transitions() -> None:

    service = MemoryService()

    service.initialize()

    service.start()

    assert service.is_running

    service.stop()

    service.dispose()


def test_dispose_clears_all_memory() -> None:

    service = MemoryService()

    item = service.store(
        memory_type=MemoryType.EPISODIC, content="a", collection="conversation:s1"
    )

    service.initialize()

    service.start()

    service.stop()

    service.dispose()

    with pytest.raises(KeyError):
        service.retrieve(item.memory_id)