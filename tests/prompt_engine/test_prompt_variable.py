import pytest

from enterprise_ai_platform.prompt_engine import PromptVariable


def test_defaults() -> None:

    variable = PromptVariable(name="question", type="string")

    assert variable.required is True

    assert variable.default_value is None

    assert variable.validation_rules == {}

    assert variable.description is None


def test_explicit_values() -> None:

    variable = PromptVariable(
        name="max_results",
        type="number",
        required=False,
        default_value=5,
        validation_rules={"minimum": 1, "maximum": 20},
        description="Maximum number of results to return.",
    )

    assert variable.default_value == 5

    assert variable.validation_rules["maximum"] == 20


def test_is_frozen() -> None:

    variable = PromptVariable(name="question", type="string")

    with pytest.raises(Exception):
        variable.name = "other"