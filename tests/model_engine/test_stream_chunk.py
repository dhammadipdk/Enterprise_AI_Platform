import pytest

from enterprise_ai_platform.model_engine import StreamChunk


def test_defaults() -> None:

    chunk = StreamChunk(request_id="r1", text="Zero dep")

    assert chunk.is_final is False

    assert chunk.metadata == {}


def test_is_frozen() -> None:

    chunk = StreamChunk(request_id="r1", text="Zero dep")

    with pytest.raises(Exception):
        chunk.text = "changed"