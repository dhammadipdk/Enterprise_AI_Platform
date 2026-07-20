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
    
    
def test_repository_loader_applies_manifest_overrides(
    tmp_path: Path,
) -> None:

    policy = tmp_path / "policy"

    policy.mkdir()

    (policy / "premium_bands.csv").write_text("band,premium\n")

    (policy / "manifest.yaml").write_text(
        "owner: Product Team\n"
        "asset_type_overrides:\n"
        "  premium_bands: reference_data\n"
    )

    loader = KnowledgeRepositoryLoader()

    repository = loader.load(tmp_path)

    domain = repository.domains[0]

    assert domain.manifest is not None

    assert domain.manifest.owner == "Product Team"

    assert len(domain.assets) == 1

    assert domain.assets[0].asset_type == "reference_data"