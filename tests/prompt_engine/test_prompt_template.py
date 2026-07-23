import pytest

from enterprise_ai_platform.prompt_engine import PromptTemplate, PromptVariable


def test_minimal_template_uses_defaults() -> None:

    template = PromptTemplate(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Explain: {{question}}",
    )

    assert template.system_prompt is None

    assert template.variables == []

    assert template.referenced_variables == []

    assert template.output_schema is None

    assert template.metadata == {}


def test_full_template() -> None:

    template = PromptTemplate(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Question: {{question}}",
        system_prompt="You are InsureAI's assistant.",
        variables=[PromptVariable(name="question", type="string")],
        referenced_variables=["question"],
        output_schema={"type": "object"},
        metadata={"persona": "explanation_agent"},
    )

    assert template.referenced_variables == ["question"]

    assert template.metadata["persona"] == "explanation_agent"


def test_is_frozen() -> None:

    template = PromptTemplate(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Explain: {{question}}",
    )

    with pytest.raises(Exception):
        template.version = "2.0.0"