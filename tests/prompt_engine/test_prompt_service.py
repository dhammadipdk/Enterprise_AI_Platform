import pytest

from enterprise_ai_platform.prompt_engine import PromptService, PromptTemplate


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


def test_validate_prompt_valid_data() -> None:

    service = PromptService()

    report = service.validate_prompt(_prompt_data())

    assert report.is_valid


def test_validate_prompt_invalid_data() -> None:

    service = PromptService()

    data = _prompt_data()

    data["user_prompt"] = "Customer asked: {{question}}, tone: {{tone}}"

    report = service.validate_prompt(data)

    assert not report.is_valid


def test_compile_prompt_does_not_register() -> None:

    service = PromptService()

    template = service.compile_prompt(_prompt_data())

    assert template.name == "explain_zero_dep"

    assert not service.prompt_exists("explain_zero_dep")


def test_register_prompt_makes_it_retrievable() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data())

    assert service.prompt_exists("explain_zero_dep")

    template = service.get_prompt("explain_zero_dep")

    assert template.version == "1.0.0"


def test_register_compiled_template_directly() -> None:

    service = PromptService()

    template = PromptTemplate(
        name="manual_prompt",
        version="1.0.0",
        user_prompt="Hello {{name}}",
    )

    service.register_compiled_template(template)

    assert service.prompt_exists("manual_prompt")


def test_get_prompt_missing_raises_key_error() -> None:

    service = PromptService()

    with pytest.raises(KeyError):
        service.get_prompt("does_not_exist")


def test_get_prompt_specific_version() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.0.0"))

    service.register_prompt(_prompt_data(version="2.0.0"))

    template = service.get_prompt("explain_zero_dep", version="1.0.0")

    assert template.version == "1.0.0"


def test_get_prompt_default_returns_latest_version() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.0.0"))

    service.register_prompt(_prompt_data(version="2.0.0"))

    template = service.get_prompt("explain_zero_dep")

    assert template.version == "2.0.0"


def test_get_prompt_latest_uses_numeric_not_string_comparison() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.9.0"))

    service.register_prompt(_prompt_data(version="1.10.0"))

    template = service.get_prompt("explain_zero_dep")

    # Plain string comparison would incorrectly pick "1.9.0" here.
    assert template.version == "1.10.0"


def test_list_prompts_returns_unique_names() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.0.0"))

    service.register_prompt(_prompt_data(version="2.0.0"))

    service.register_prompt(_prompt_data(name="other_prompt"))

    assert service.list_prompts() == ["explain_zero_dep", "other_prompt"]


def test_list_versions_sorted_numerically() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data(version="1.9.0"))

    service.register_prompt(_prompt_data(version="1.2.0"))

    service.register_prompt(_prompt_data(version="1.10.0"))

    assert service.list_versions("explain_zero_dep") == [
        "1.2.0",
        "1.9.0",
        "1.10.0",
    ]


def test_resolve_variables() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data())

    result = service.resolve_variables(
        "explain_zero_dep",
        {"question": "hi", "context": "policy text"},
    )

    assert result.is_valid

    assert result.values["question"] == "hi"


def test_render_prompt_full_pipeline() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data())

    instance = service.render_prompt(
        "explain_zero_dep",
        {
            "question": "Zero dep matlab kya hai?",
            "context": "Zero dep covers full part replacement cost.",
        },
    )

    assert "Zero dep matlab kya hai?" in instance.rendered_user_prompt

    assert instance.rendered_system_prompt == (
        "You are InsureAI's explanation assistant."
    )


def test_render_prompt_missing_required_value_raises() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data())

    with pytest.raises(ValueError, match="context"):
        service.render_prompt("explain_zero_dep", {"question": "hi"})


def test_load_from_knowledge_registers_every_prompt_asset() -> None:

    service = PromptService()

    fake_knowledge_store = {
        "explain_zero_dep": _prompt_data(),
        "explain_ncb": _prompt_data(name="explain_ncb"),
    }

    def fake_list_assets(repository, domain):
        assert repository == "platform"
        assert domain == "prompts"
        return list(fake_knowledge_store.keys())

    def fake_load_asset_content(repository, domain, asset):
        return fake_knowledge_store[asset]

    templates = service.load_from_knowledge(
        fake_list_assets, fake_load_asset_content, "platform"
    )

    assert len(templates) == 2

    assert service.prompt_exists("explain_zero_dep")

    assert service.prompt_exists("explain_ncb")


def test_load_from_knowledge_uses_custom_domain() -> None:

    service = PromptService()

    calls = []

    def fake_list_assets(repository, domain):
        calls.append((repository, domain))
        return []

    def fake_load_asset_content(repository, domain, asset):
        return {}

    service.load_from_knowledge(
        fake_list_assets,
        fake_load_asset_content,
        "platform",
        domain="custom_prompts",
    )

    assert calls == [("platform", "custom_prompts")]


def test_lifecycle_transitions() -> None:

    service = PromptService()

    service.initialize()

    service.start()

    assert service.is_running

    service.stop()

    service.dispose()


def test_dispose_clears_registered_prompts() -> None:

    service = PromptService()

    service.register_prompt(_prompt_data())

    service.initialize()

    service.start()

    service.stop()

    service.dispose()

    assert not service.prompt_exists("explain_zero_dep")