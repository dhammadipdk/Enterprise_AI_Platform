import pytest

from enterprise_ai_platform.prompt_engine import (
    PromptCompiler,
    PromptDefinition,
    PromptRenderer,
    PromptVariable,
    VariableResolver,
)


def _compiled_template():

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        system_prompt="You are InsureAI's explanation assistant.",
        user_prompt=(
            "Customer asked: {{question}}\n"
            "Retrieved context: {{context}}"
        ),
        variables=[
            PromptVariable(name="question", type="string"),
            PromptVariable(name="context", type="string"),
        ],
    )

    return PromptCompiler().compile(definition)


def test_render_substitutes_all_variables() -> None:

    template = _compiled_template()

    resolution = VariableResolver().resolve(
        template,
        {
            "question": "Zero dep matlab kya hai?",
            "context": "Zero dep covers full part replacement cost.",
        },
    )

    instance = PromptRenderer().render(template, resolution)

    assert "Zero dep matlab kya hai?" in instance.rendered_user_prompt

    assert (
        "Zero dep covers full part replacement cost."
        in instance.rendered_user_prompt
    )

    assert "{{question}}" not in instance.rendered_user_prompt

    assert instance.rendered_system_prompt == (
        "You are InsureAI's explanation assistant."
    )


def test_render_stores_resolved_variables_on_instance() -> None:

    template = _compiled_template()

    resolution = VariableResolver().resolve(
        template,
        {"question": "hi", "context": "policy text"},
    )

    instance = PromptRenderer().render(template, resolution)

    assert instance.resolved_variables == {
        "question": "hi",
        "context": "policy text",
    }


def test_render_refuses_when_resolution_has_errors() -> None:

    template = _compiled_template()

    # Missing required "context" -> resolution has an error.
    resolution = VariableResolver().resolve(template, {"question": "hi"})

    assert not resolution.is_valid

    with pytest.raises(ValueError, match="context"):
        PromptRenderer().render(template, resolution)


def test_render_with_no_system_prompt() -> None:

    definition = PromptDefinition(
        name="minimal_prompt",
        version="1.0.0",
        user_prompt="Hello {{name}}",
        variables=[PromptVariable(name="name", type="string")],
    )

    template = PromptCompiler().compile(definition)

    resolution = VariableResolver().resolve(template, {"name": "Rahul"})

    instance = PromptRenderer().render(template, resolution)

    assert instance.rendered_system_prompt is None

    assert instance.rendered_user_prompt == "Hello Rahul"


def test_render_optional_variable_with_no_value_becomes_empty_string() -> None:

    definition = PromptDefinition(
        name="optional_prompt",
        version="1.0.0",
        user_prompt="Question: {{question}} (Tone: {{tone}})",
        variables=[
            PromptVariable(name="question", type="string"),
            PromptVariable(name="tone", type="string", required=False),
        ],
    )

    template = PromptCompiler().compile(definition)

    resolution = VariableResolver().resolve(
        template, {"question": "hi"}
    )

    assert resolution.is_valid

    instance = PromptRenderer().render(template, resolution)

    assert instance.rendered_user_prompt == "Question: hi (Tone: )"

    assert "None" not in instance.rendered_user_prompt


def test_render_is_deterministic() -> None:

    template = _compiled_template()

    resolution = VariableResolver().resolve(
        template,
        {"question": "hi", "context": "policy text"},
    )

    first = PromptRenderer().render(template, resolution)

    second = PromptRenderer().render(template, resolution)

    assert first.rendered_user_prompt == second.rendered_user_prompt

    assert first.rendered_system_prompt == second.rendered_system_prompt


def test_render_passes_through_context() -> None:

    template = _compiled_template()

    resolution = VariableResolver().resolve(
        template,
        {"question": "hi", "context": "policy text"},
    )

    instance = PromptRenderer().render(
        template, resolution, context={"session_id": "abc123"}
    )

    assert instance.context == {"session_id": "abc123"}