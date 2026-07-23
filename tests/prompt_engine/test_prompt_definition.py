import pytest

from enterprise_ai_platform.prompt_engine import (
    PromptDefinition,
    PromptVariable,
)


def test_minimal_definition_uses_defaults() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Explain: {{question}}",
    )

    assert definition.description is None

    assert definition.system_prompt is None

    assert definition.variables == []

    assert definition.output_schema is None

    assert definition.metadata == {}


def test_full_definition() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        description="Explains zero depreciation cover.",
        system_prompt="You are InsureAI's explanation assistant.",
        user_prompt="Question: {{question}}\nContext: {{context}}",
        variables=[
            PromptVariable(name="question", type="string"),
            PromptVariable(name="context", type="string"),
        ],
        output_schema={"type": "object"},
        metadata={"domain": "policy", "persona": "explanation_agent"},
    )

    assert len(definition.variables) == 2

    assert definition.metadata["persona"] == "explanation_agent"


def test_is_frozen() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Explain: {{question}}",
    )

    with pytest.raises(Exception):
        definition.version = "2.0.0"