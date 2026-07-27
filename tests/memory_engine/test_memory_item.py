import pytest

from enterprise_ai_platform.memory_engine import MemoryItem, MemoryType


def test_defaults() -> None:

    item = MemoryItem(
        memory_type=MemoryType.EPISODIC,
        content="Customer asked about zero dep.",
        collection="conversation:s1",
    )

    assert item.memory_id

    assert item.embedding is None

    assert item.metadata == {}

    assert item.owner is None

    assert item.expires_at is None

    assert item.version == 1


def test_memory_ids_are_unique() -> None:

    a = MemoryItem(
        memory_type=MemoryType.EPISODIC, content="a", collection="c1"
    )

    b = MemoryItem(
        memory_type=MemoryType.EPISODIC, content="b", collection="c1"
    )

    assert a.memory_id != b.memory_id


def test_is_frozen() -> None:

    item = MemoryItem(
        memory_type=MemoryType.EPISODIC, content="a", collection="c1"
    )

    with pytest.raises(Exception):
        item.content = "changed"