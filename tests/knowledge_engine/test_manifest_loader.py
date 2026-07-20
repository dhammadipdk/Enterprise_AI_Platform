from pathlib import Path

from enterprise_ai_platform.knowledge_engine import ManifestLoader


def test_manifest_loader_returns_none_when_absent(tmp_path: Path) -> None:

    loader = ManifestLoader()

    manifest = loader.load(tmp_path)

    assert manifest is None


def test_manifest_loader_parses_yaml(tmp_path: Path) -> None:

    (tmp_path / "manifest.yaml").write_text(
        "owner: Product & Knowledge Engineering Team\n"
        "description: Motor insurance policy domain.\n"
        "version: 1.0.0\n"
        "tags:\n"
        "  - insurance\n"
        "  - motor\n"
        "asset_type_overrides:\n"
        "  premium_bands: reference_data\n"
    )

    loader = ManifestLoader()

    manifest = loader.load(tmp_path)

    assert manifest is not None

    assert manifest.owner == "Product & Knowledge Engineering Team"

    assert manifest.version == "1.0.0"

    assert manifest.tags == ["insurance", "motor"]

    assert manifest.asset_type_overrides == {
        "premium_bands": "reference_data"
    }


def test_manifest_loader_handles_empty_file(tmp_path: Path) -> None:

    (tmp_path / "manifest.yaml").write_text("")

    loader = ManifestLoader()

    manifest = loader.load(tmp_path)

    assert manifest is not None

    assert manifest.owner is None

    assert manifest.tags == []