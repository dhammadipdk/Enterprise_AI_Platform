import pytest

from enterprise_ai_platform.prompt_engine import PromptRegistry, PromptTemplate


def _template(name="explain_zero_dep", version="1.0.0"):

    return PromptTemplate(
        name=name,
        version=version,
        user_prompt="Explain: {{question}}",
    )


def test_register_and_get() -> None:

    registry = PromptRegistry()

    registry.register("explain_zero_dep@1.0.0", _template())

    retrieved = registry.get("explain_zero_dep@1.0.0")

    assert retrieved.name == "explain_zero_dep"


def test_exists() -> None:

    registry = PromptRegistry()

    assert not registry.exists("explain_zero_dep@1.0.0")

    registry.register("explain_zero_dep@1.0.0", _template())

    assert registry.exists("explain_zero_dep@1.0.0")


def test_get_missing_raises_key_error() -> None:

    registry = PromptRegistry()

    with pytest.raises(KeyError):
        registry.get("does_not_exist@1.0.0")


def test_names_lists_all_keys() -> None:

    registry = PromptRegistry()

    registry.register("a@1.0.0", _template(name="a"))

    registry.register("b@1.0.0", _template(name="b"))

    assert registry.names() == ["a@1.0.0", "b@1.0.0"]


def test_clear_removes_everything() -> None:

    registry = PromptRegistry()

    registry.register("explain_zero_dep@1.0.0", _template())

    registry.clear()

    assert registry.names() == []