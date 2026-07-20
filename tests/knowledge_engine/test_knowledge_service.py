from pathlib import Path

import pytest

from enterprise_ai_platform.knowledge_engine import KnowledgeService


def _build_sample_repository(root: Path) -> None:

    policy = root / "policy"

    policy.mkdir()

    (policy / "canonical_schema.csv").write_text("id,name\n")

    (policy / "glossary.csv").write_text("term,definition\n")

    (policy / "README.md").write_text("# Policy")

    claims = root / "claims"

    claims.mkdir()

    (claims / "entity_catalog.csv").write_text("id,entity\n")


def test_lifecycle_transitions() -> None:

    service = KnowledgeService()

    service.initialize()

    service.start()

    assert service.is_running

    service.stop()

    service.dispose()


def test_start_before_initialize_raises() -> None:

    service = KnowledgeService()

    with pytest.raises(ValueError):
        service.start()


def test_load_repository(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    repository = service.load_repository("insurance", tmp_path)

    assert len(repository.domains) == 2

    assert service.repository_exists("insurance")

    assert service.list_repositories() == ["insurance"]


def test_get_repository_unknown_raises() -> None:

    service = KnowledgeService()

    with pytest.raises(KeyError):
        service.get_repository("insurance")


def test_list_domains_and_assets(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    assert sorted(service.list_domains("insurance")) == ["claims", "policy"]

    assert sorted(service.list_assets("insurance", "policy")) == [
        "README",
        "canonical_schema",
        "glossary",
    ]


def test_get_domain_missing_raises(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    with pytest.raises(KeyError):
        service.get_domain("insurance", "vehicle")


def test_get_asset_missing_raises(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    with pytest.raises(KeyError):
        service.get_asset("insurance", "policy", "does_not_exist")


def test_repository_statistics(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    stats = service.repository_statistics("insurance")

    assert stats["domain_count"] == 2

    assert stats["asset_count"] == 4

    assert stats["asset_types"]["schema"] == 1

    assert stats["asset_types"]["glossary"] == 1

    assert stats["asset_types"]["documentation"] == 1

    assert stats["asset_types"]["catalog"] == 1


def test_reload_repository_replaces_content(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    vehicle = tmp_path / "vehicle"

    vehicle.mkdir()

    (vehicle / "entity_catalog.csv").write_text("id,vehicle\n")

    service.reload_repository("insurance", tmp_path)

    assert sorted(service.list_domains("insurance")) == [
        "claims",
        "policy",
        "vehicle",
    ]