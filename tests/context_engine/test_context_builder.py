import pytest

from enterprise_ai_platform.context_engine import (
    ContextBuilder,
    ContextCategory,
    ContextFragment,
    ContextSource,
)


def _fragment(category, label, content, priority=0):

    return ContextFragment(
        source=ContextSource.KNOWLEDGE,
        category=category,
        label=label,
        content=content,
        priority=priority,
    )


def test_build_places_fragments_in_correct_buckets() -> None:

    builder = ContextBuilder()

    context = builder.build(
        [
            _fragment(
                ContextCategory.KNOWLEDGE,
                "retrieved_documents",
                ["Zero dep covers full part cost."],
            ),
            _fragment(
                ContextCategory.USER,
                "profile",
                {"tier": "premium"},
            ),
        ]
    )

    assert context.knowledge_context["retrieved_documents"] == [
        "Zero dep covers full part cost."
    ]

    assert context.user_context["profile"] == {"tier": "premium"}


def test_build_resolves_conflict_by_priority() -> None:

    builder = ContextBuilder()

    context = builder.build(
        [
            _fragment(
                ContextCategory.USER, "profile", {"tier": "basic"}, priority=1
            ),
            _fragment(
                ContextCategory.USER,
                "profile",
                {"tier": "premium"},
                priority=5,
            ),
        ]
    )

    assert context.user_context["profile"] == {"tier": "premium"}


def test_build_conflict_resolution_is_order_independent() -> None:

    builder = ContextBuilder()

    context_a = builder.build(
        [
            _fragment(
                ContextCategory.USER, "profile", {"tier": "basic"}, priority=1
            ),
            _fragment(
                ContextCategory.USER,
                "profile",
                {"tier": "premium"},
                priority=5,
            ),
        ]
    )

    context_b = builder.build(
        [
            _fragment(
                ContextCategory.USER,
                "profile",
                {"tier": "premium"},
                priority=5,
            ),
            _fragment(
                ContextCategory.USER, "profile", {"tier": "basic"}, priority=1
            ),
        ]
    )

    assert context_a.user_context == context_b.user_context


def test_empty_label_is_a_validation_error() -> None:

    builder = ContextBuilder()

    fragments = [_fragment(ContextCategory.USER, "", {"tier": "basic"})]

    report = builder.validate(fragments)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "EMPTY_FRAGMENT_LABEL" in codes


def test_build_raises_on_empty_label() -> None:

    builder = ContextBuilder()

    fragments = [_fragment(ContextCategory.USER, "", {"tier": "basic"})]

    with pytest.raises(ValueError, match="empty label"):
        builder.build(fragments)


def test_max_fragments_exceeded_is_a_validation_error() -> None:

    builder = ContextBuilder()

    fragments = [
        _fragment(ContextCategory.USER, f"item_{i}", i) for i in range(5)
    ]

    report = builder.validate(fragments, max_fragments=3)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "OVERSIZED_CONTEXT" in codes


def test_within_max_fragments_is_valid() -> None:

    builder = ContextBuilder()

    fragments = [
        _fragment(ContextCategory.USER, f"item_{i}", i) for i in range(3)
    ]

    report = builder.validate(fragments, max_fragments=3)

    assert report.is_valid


def test_unresolved_priority_tie_is_a_warning_not_an_error() -> None:

    builder = ContextBuilder()

    fragments = [
        _fragment(ContextCategory.USER, "profile", {"tier": "basic"}),
        _fragment(ContextCategory.USER, "profile", {"tier": "premium"}),
    ]

    report = builder.validate(fragments)

    assert report.is_valid  # warnings don't block validity

    codes = {issue.code for issue in report.warnings}

    assert "UNRESOLVED_PRIORITY_TIE" in codes


def test_equal_priority_same_content_is_not_a_tie_warning() -> None:

    builder = ContextBuilder()

    fragments = [
        _fragment(ContextCategory.USER, "profile", {"tier": "basic"}),
        _fragment(ContextCategory.USER, "profile", {"tier": "basic"}),
    ]

    report = builder.validate(fragments)

    assert report.warnings == []


def test_different_labels_never_conflict() -> None:

    builder = ContextBuilder()

    context = builder.build(
        [
            _fragment(ContextCategory.KNOWLEDGE, "docs", ["a"]),
            _fragment(ContextCategory.KNOWLEDGE, "ontology_facts", ["b"]),
        ]
    )

    assert context.knowledge_context == {
        "docs": ["a"],
        "ontology_facts": ["b"],
    }


def test_empty_fragment_list_produces_empty_context() -> None:

    builder = ContextBuilder()

    context = builder.build([])

    assert context.knowledge_context == {}

    assert context.user_context == {}