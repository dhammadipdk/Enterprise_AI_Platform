import pytest

from enterprise_ai_platform.prompt_engine import (
    PromptTemplate,
    PromptVariable,
    PromptVersionComparator,
)


def _template_v1():

    return PromptTemplate(
        name="explain_zero_dep",
        version="1.0.0",
        system_prompt="You are InsureAI's explanation assistant.",
        user_prompt="Q: {{question}} Ctx: {{context}}",
        variables=[
            PromptVariable(name="question", type="string"),
            PromptVariable(name="context", type="string"),
        ],
    )


def _template_v2():

    return PromptTemplate(
        name="explain_zero_dep",
        version="2.0.0",
        system_prompt="You are InsureAI's explanation assistant. Be concise.",
        user_prompt="Q: {{question}} Ctx: {{context}} Tone: {{tone}}",
        variables=[
            PromptVariable(name="question", type="string"),
            PromptVariable(
                name="context",
                type="string",
                required=False,
                default_value="",
            ),
            PromptVariable(
                name="tone",
                type="string",
                required=False,
                default_value="neutral",
            ),
        ],
    )


def test_compare_detects_added_variable() -> None:

    diff = PromptVersionComparator().compare(_template_v1(), _template_v2())

    assert diff.added_variables == ["tone"]


def test_compare_detects_changed_variable() -> None:

    diff = PromptVersionComparator().compare(_template_v1(), _template_v2())

    assert diff.changed_variables == ["context"]

    assert diff.removed_variables == []


def test_compare_detects_prompt_text_changes() -> None:

    diff = PromptVersionComparator().compare(_template_v1(), _template_v2())

    assert diff.system_prompt_changed is True

    assert diff.user_prompt_changed is True


def test_compare_identical_templates_has_no_changes() -> None:

    template = _template_v1()

    diff = PromptVersionComparator().compare(template, template)

    assert not diff.has_changes

    assert diff.added_variables == []

    assert diff.removed_variables == []

    assert diff.changed_variables == []


def test_compare_has_changes_true_when_something_differs() -> None:

    diff = PromptVersionComparator().compare(_template_v1(), _template_v2())

    assert diff.has_changes


def test_compare_different_prompt_names_raises() -> None:

    other = PromptTemplate(
        name="other_prompt",
        version="1.0.0",
        user_prompt="Hello",
    )

    with pytest.raises(ValueError, match="different prompts"):
        PromptVersionComparator().compare(_template_v1(), other)


def test_compare_reports_removed_variable() -> None:

    v1 = PromptTemplate(
        name="test_prompt",
        version="1.0.0",
        user_prompt="{{a}} {{b}}",
        variables=[
            PromptVariable(name="a", type="string"),
            PromptVariable(name="b", type="string"),
        ],
    )

    v2 = PromptTemplate(
        name="test_prompt",
        version="2.0.0",
        user_prompt="{{a}}",
        variables=[PromptVariable(name="a", type="string")],
    )

    diff = PromptVersionComparator().compare(v1, v2)

    assert diff.removed_variables == ["b"]