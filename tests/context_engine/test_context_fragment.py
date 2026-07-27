import pytest

from enterprise_ai_platform.context_engine import (
    ContextCategory,
    ContextFragment,
    ContextSource,
)


def test_defaults() -> None:

    fragment = ContextFragment(
        source=ContextSource.KNOWLEDGE,
        category=ContextCategory.KNOWLEDGE,
        label="retrieved_documents",
        content=["doc1", "doc2"],
    )

    assert fragment.fragment_id

    assert fragment.priority == 0

    assert fragment.metadata == {}


def test_is_frozen() -> None:

    fragment = ContextFragment(
        source=ContextSource.KNOWLEDGE,
        category=ContextCategory.KNOWLEDGE,
        label="retrieved_documents",
        content=["doc1"],
    )

    with pytest.raises(Exception):
        fragment.label = "changed"