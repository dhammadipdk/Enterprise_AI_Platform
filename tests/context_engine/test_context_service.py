import pytest

from enterprise_ai_platform.context_engine import (
    ContextCategory,
    ContextFragment,
    ContextService,
    ContextSource,
    PlatformContext,
)


def _fragment(category, label, content, source=ContextSource.KNOWLEDGE):

    return ContextFragment(
        source=source, category=category, label=label, content=content
    )


def test_build_and_validate() -> None:

    service = ContextService()

    fragments = [
        _fragment(
            ContextCategory.KNOWLEDGE,
            "retrieved_documents",
            ["Zero dep covers full part cost."],
        ),
    ]

    report = service.validate(fragments)

    assert report.is_valid

    context = service.build(fragments)

    assert context.knowledge_context["retrieved_documents"] == [
        "Zero dep covers full part cost."
    ]


def test_build_raises_on_invalid_fragments() -> None:

    service = ContextService()

    with pytest.raises(ValueError):
        service.build([_fragment(ContextCategory.USER, "", {})])


def test_list_sources_reflects_most_recent_build() -> None:

    service = ContextService()

    assert service.list_sources() == []

    service.build(
        [
            _fragment(
                ContextCategory.KNOWLEDGE,
                "docs",
                ["a"],
                source=ContextSource.KNOWLEDGE,
            ),
            _fragment(
                ContextCategory.MEMORY,
                "summary",
                "prior conversation",
                source=ContextSource.MEMORY,
            ),
        ]
    )

    assert service.list_sources() == ["knowledge", "memory"]


def test_merge_override_wins_conflicts_base_survives_elsewhere() -> None:

    service = ContextService()

    base = service.build(
        [
            _fragment(ContextCategory.USER, "profile", {"tier": "basic"}),
            _fragment(ContextCategory.USER, "region", "IN"),
        ]
    )

    override = service.build(
        [_fragment(ContextCategory.USER, "profile", {"tier": "premium"})]
    )

    merged = service.merge(base, override)

    assert merged.user_context["profile"] == {"tier": "premium"}

    assert merged.user_context["region"] == "IN"


def test_serialize_and_deserialize_round_trip() -> None:

    service = ContextService()

    context = service.build(
        [
            _fragment(
                ContextCategory.KNOWLEDGE,
                "retrieved_documents",
                ["doc1"],
            ),
        ]
    )

    serialized = service.serialize(context)

    assert isinstance(serialized, str)

    restored = service.deserialize(serialized)

    assert restored.knowledge_context == context.knowledge_context

    assert restored.context_id == context.context_id


def test_statistics() -> None:

    service = ContextService()

    context = service.build(
        [
            _fragment(ContextCategory.KNOWLEDGE, "docs", ["a"]),
            _fragment(ContextCategory.KNOWLEDGE, "facts", ["b"]),
            _fragment(ContextCategory.USER, "profile", {"tier": "premium"}),
        ]
    )

    stats = service.statistics(context)

    assert stats["context_id"] == context.context_id

    assert stats["total_entries"] == 3

    assert stats["entries_per_category"]["knowledge"] == 2

    assert stats["entries_per_category"]["user"] == 1

    assert stats["entries_per_category"]["memory"] == 0


def test_lifecycle_transitions() -> None:

    service = ContextService()

    service.initialize()

    service.start()

    assert service.is_running

    service.stop()

    service.dispose()