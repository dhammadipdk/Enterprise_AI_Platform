from pathlib import Path

from enterprise_ai_platform.knowledge_engine import (
    KnowledgeAsset,
    KnowledgeDomain,
    KnowledgeRepository,
    RepositoryValidator,
)


def test_valid_repository_has_no_errors(tmp_path: Path) -> None:

    (tmp_path / "canonical_schema.csv").write_text("id,name\n")

    (tmp_path / "README.md").write_text("# Policy")

    policy = KnowledgeDomain(
        name="policy",
        assets=[
            KnowledgeAsset(
                name="canonical_schema",
                asset_type="schema",
                path=tmp_path / "canonical_schema.csv",
            ),
            KnowledgeAsset(
                name="README",
                asset_type="documentation",
                path=tmp_path / "README.md",
            ),
        ],
    )

    repository = KnowledgeRepository(domains=[policy])

    report = RepositoryValidator().validate(repository)

    assert report.errors == []


def test_empty_repository_is_an_error() -> None:

    repository = KnowledgeRepository(domains=[])

    report = RepositoryValidator().validate(repository)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "EMPTY_REPOSITORY" in codes


def test_empty_domain_is_an_error() -> None:

    empty_domain = KnowledgeDomain(name="claims", assets=[])

    repository = KnowledgeRepository(domains=[empty_domain])

    report = RepositoryValidator().validate(repository)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "EMPTY_DOMAIN" in codes


def test_duplicate_asset_names_are_an_error(tmp_path: Path) -> None:

    (tmp_path / "glossary.csv").write_text("term,definition\n")

    (tmp_path / "glossary.json").write_text("{}")

    domain = KnowledgeDomain(
        name="policy",
        assets=[
            KnowledgeAsset(
                name="glossary",
                asset_type="glossary",
                path=tmp_path / "glossary.csv",
            ),
            KnowledgeAsset(
                name="glossary",
                asset_type="glossary",
                path=tmp_path / "glossary.json",
            ),
        ],
    )

    repository = KnowledgeRepository(domains=[domain])

    report = RepositoryValidator().validate(repository)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "DUPLICATE_ASSET_NAME" in codes


def test_missing_asset_path_is_an_error(tmp_path: Path) -> None:

    domain = KnowledgeDomain(
        name="policy",
        assets=[
            KnowledgeAsset(
                name="canonical_schema",
                asset_type="schema",
                path=tmp_path / "does_not_exist.csv",
            ),
        ],
    )

    repository = KnowledgeRepository(domains=[domain])

    report = RepositoryValidator().validate(repository)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "MISSING_ASSET_PATH" in codes


def test_missing_documentation_is_a_warning_not_an_error(
    tmp_path: Path,
) -> None:

    (tmp_path / "entity_catalog.csv").write_text("id,entity\n")

    domain = KnowledgeDomain(
        name="claims",
        assets=[
            KnowledgeAsset(
                name="entity_catalog",
                asset_type="catalog",
                path=tmp_path / "entity_catalog.csv",
            ),
        ],
    )

    repository = KnowledgeRepository(domains=[domain])

    report = RepositoryValidator().validate(repository)

    assert report.is_valid

    codes = {issue.code for issue in report.warnings}

    assert "MISSING_DOCUMENTATION" in codes