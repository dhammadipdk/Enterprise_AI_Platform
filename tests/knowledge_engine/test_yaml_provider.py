from pathlib import Path

from enterprise_ai_platform.knowledge_engine import YAMLProvider


def test_yaml_provider_load(tmp_path: Path) -> None:

    yaml_file = tmp_path / "prompt.yaml"

    yaml_file.write_text(
        "name: explain_zero_dep\n"
        "version: \"1.0.0\"\n"
        "user_prompt: |\n"
        "  Explain: {{question}}\n"
    )

    provider = YAMLProvider()

    data = provider.load(yaml_file)

    assert data["name"] == "explain_zero_dep"

    assert data["version"] == "1.0.0"

    assert "{{question}}" in data["user_prompt"]


def test_yaml_provider_save_and_reload(tmp_path: Path) -> None:

    yaml_file = tmp_path / "roundtrip.yaml"

    provider = YAMLProvider()

    original = {
        "name": "roundtrip_prompt",
        "version": "1.0.0",
        "variables": [{"name": "x", "type": "string"}],
    }

    provider.save(original, yaml_file)

    reloaded = provider.load(yaml_file)

    assert reloaded == original