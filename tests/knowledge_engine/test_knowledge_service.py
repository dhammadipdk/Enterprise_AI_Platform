from pathlib import Path

import pytest

from enterprise_ai_platform.knowledge_engine import KnowledgeService
from enterprise_ai_platform.framework.base import BaseProvider


def _build_sample_repository(root: Path) -> None:

    policy = root / "policy"

    policy.mkdir()

    (policy / "canonical_schema.csv").write_text(
        "id,name\n1,Comprehensive\n"
    )

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
    


def test_load_asset_content_csv(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    content = service.load_asset_content(
        "insurance", "policy", "canonical_schema"
    )

    assert content == [{"id": 1, "name": "Comprehensive"}]


def test_load_asset_content_markdown(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    content = service.load_asset_content("insurance", "policy", "README")

    assert content == "# Policy"


def test_load_asset_content_unsupported_extension_raises(
    tmp_path: Path,
) -> None:

    policy = tmp_path / "policy"

    policy.mkdir()

    (policy / "notes.txt").write_text("unsupported")

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    with pytest.raises(ValueError):
        service.load_asset_content("insurance", "policy", "notes")


def test_register_custom_provider(tmp_path: Path) -> None:

    class UpperCaseTextProvider(BaseProvider):

        def load(self, path: Path) -> str:
            return path.read_text().upper()

        def save(self, data: str, path: Path) -> None:
            path.write_text(data)

    policy = tmp_path / "policy"

    policy.mkdir()

    (policy / "notes.txt").write_text("hello")

    service = KnowledgeService()

    service.register_provider(".txt", UpperCaseTextProvider())

    service.load_repository("insurance", tmp_path)

    content = service.load_asset_content("insurance", "policy", "notes")

    assert content == "HELLO"
    
    
def test_validate_repository(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    report = service.validate_repository("insurance")

    assert report.errors == []

    codes = {issue.code for issue in report.warnings}

    assert "MISSING_DOCUMENTATION" in codes
    
def test_get_manifest_when_absent(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    assert service.get_manifest("insurance", "policy") is None
    
def test_chunk_asset_csv(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    chunks = service.chunk_asset("insurance", "policy", "canonical_schema")

    assert len(chunks) == 1

    assert chunks[0].content == "id: 1\nname: Comprehensive"

    assert chunks[0].repository == "insurance"

    assert chunks[0].domain == "policy"

    assert chunks[0].asset == "canonical_schema"


def test_chunk_asset_markdown(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    chunks = service.chunk_asset("insurance", "policy", "README")

    assert len(chunks) == 1

    assert chunks[0].content == "# Policy"


def test_chunk_domain_covers_all_assets(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    chunks = service.chunk_domain("insurance", "policy")

    assert len(chunks) == 2


def test_chunk_repository_covers_all_domains(tmp_path: Path) -> None:

    _build_sample_repository(tmp_path)

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    chunks = service.chunk_repository("insurance")

    assert len(chunks) == 2


def test_chunk_asset_unsupported_extension_raises(tmp_path: Path) -> None:

    policy = tmp_path / "policy"

    policy.mkdir()

    (policy / "notes.txt").write_text("unsupported")

    service = KnowledgeService()

    service.load_repository("insurance", tmp_path)

    with pytest.raises(ValueError):
        service.chunk_asset("insurance", "policy", "notes")