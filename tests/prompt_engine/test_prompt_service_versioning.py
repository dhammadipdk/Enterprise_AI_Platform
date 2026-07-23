import pytest

from enterprise_ai_platform.prompt_engine import PromptService


def _prompt_data(name="explain_zero_dep", version="1.0.0"):

    return {
        "name": name,
        "version": version,
        "system_prompt": "You are InsureAI's explanation assistant.",
        "user_prompt": (
            "Customer asked: {{question}}\n"
            "Retrieved context: {{context}}"
        ),
        "variables": [
            {"name": "question", "type": "string", "required": True},
            {"name": "context", "type": "string", "required": True},
        ],
    }


def test_compare_versions() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.0.0"))

    data_v2 = _prompt_data(version="2.0.0")

    data_v2["variables"].append(
        {"name": "tone", "type": "string", "required": False}
    )

    data_v2["user_prompt"] += "\nTone: {{tone}}"

    service.register_prompt(data_v2)

    diff = service.compare_versions("explain_zero_dep", "1.0.0", "2.0.0")

    assert diff.added_variables == ["tone"]

    assert diff.user_prompt_changed is True


def test_deprecate_marks_version() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data())

    assert not service.is_deprecated("explain_zero_dep", "1.0.0")

    service.deprecate(
        "explain_zero_dep", "1.0.0", reason="Superseded by v2.0.0"
    )

    assert service.is_deprecated("explain_zero_dep", "1.0.0")

    info = service.get_deprecation_info("explain_zero_dep", "1.0.0")

    assert info.reason == "Superseded by v2.0.0"


def test_deprecate_missing_version_raises() -> None:

    service = PromptService()

    with pytest.raises(KeyError):
        service.deprecate("does_not_exist", "1.0.0")


def test_undeprecate_removes_status() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data())

    service.deprecate("explain_zero_dep", "1.0.0")

    service.undeprecate("explain_zero_dep", "1.0.0")

    assert not service.is_deprecated("explain_zero_dep", "1.0.0")

    assert service.get_deprecation_info("explain_zero_dep", "1.0.0") is None


def test_get_prompt_latest_skips_deprecated_version() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.0.0"))

    service.register_prompt(_prompt_data(version="2.0.0"))

    service.deprecate("explain_zero_dep", "2.0.0")

    template = service.get_prompt("explain_zero_dep")

    assert template.version == "1.0.0"


def test_get_prompt_explicit_version_still_returns_deprecated() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.0.0"))

    service.deprecate("explain_zero_dep", "1.0.0")

    template = service.get_prompt("explain_zero_dep", version="1.0.0")

    assert template.version == "1.0.0"


def test_get_prompt_latest_falls_back_when_all_versions_deprecated() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.0.0"))

    service.register_prompt(_prompt_data(version="2.0.0"))

    service.deprecate("explain_zero_dep", "1.0.0")

    service.deprecate("explain_zero_dep", "2.0.0")

    template = service.get_prompt("explain_zero_dep")

    assert template.version == "2.0.0"


def test_list_versions_still_includes_deprecated() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.0.0"))

    service.register_prompt(_prompt_data(version="2.0.0"))

    service.deprecate("explain_zero_dep", "1.0.0")

    assert service.list_versions("explain_zero_dep") == ["1.0.0", "2.0.0"]


def test_dispose_clears_deprecation_state() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data())

    service.deprecate("explain_zero_dep", "1.0.0")

    service.initialize()

    service.start()

    service.stop()

    service.dispose()

    assert not service.prompt_exists("explain_zero_dep")