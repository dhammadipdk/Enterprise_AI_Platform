from pathlib import Path

from enterprise_ai_platform.knowledge_engine import (
    KnowledgeAsset,
    KnowledgeDomain,
    KnowledgeRepository,
)


def test_repository_model() -> None:

    asset = KnowledgeAsset(
        name="canonical_schema",
        path=Path("policy/canonical_schema.csv"),
    )

    domain = KnowledgeDomain(
        name="policy",
        assets=[asset],
    )

    repository = KnowledgeRepository(
        domains=[domain],
    )

    assert repository.domains[0].name == "policy"

    assert repository.domains[0].assets[0].name == "canonical_schema"