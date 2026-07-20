from pathlib import Path

from enterprise_ai_platform.knowledge_engine import (
    KnowledgeRepositoryLoader,
)


def test_repository_loader(tmp_path: Path) -> None:

    policy = tmp_path / "policy"

    policy.mkdir()

    (policy / "canonical_schema.csv").write_text("id,name\n")

    (policy / "README.md").write_text("# Policy")

    loader = KnowledgeRepositoryLoader()

    repository = loader.load(tmp_path)

    assert len(repository.domains) == 1

    domain = repository.domains[0]

    assert domain.name == "policy"

    assert len(domain.assets) == 2

    assert domain.assets[0].asset_type in {
        "schema",
        "documentation",
    }