import pytest

from enterprise_ai_platform.prompt_engine import (
    PromptCompiler,
    PromptDefinition,
    PromptVariable,
)


def _valid_definition() -> PromptDefinition:

    return PromptDefinition(
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


def test_valid_definition_has_no_errors() -> None:

    report = PromptCompiler().validate(_valid_definition())

    assert report.is_valid

    assert report.errors == []


def test_compile_valid_definition_produces_template() -> None:

    template = PromptCompiler().compile(_valid_definition())

    assert template.name == "explain_zero_dep"

    assert template.referenced_variables == ["question", "context"]


def test_missing_variable_is_an_error() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Customer asked: {{question}}, tone: {{tone}}",
        variables=[PromptVariable(name="question", type="string")],
    )

    report = PromptCompiler().validate(definition)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "MISSING_VARIABLE" in codes


def test_missing_variable_blocks_compilation() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Customer asked: {{tone}}",
    )

    with pytest.raises(ValueError, match="tone"):
        PromptCompiler().compile(definition)


def test_unused_variable_is_a_warning_not_an_error() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Customer asked: {{question}}",
        variables=[
            PromptVariable(name="question", type="string"),
            PromptVariable(name="tone", type="string"),
        ],
    )

    report = PromptCompiler().validate(definition)

    assert report.is_valid

    codes = {issue.code for issue in report.warnings}

    assert "UNUSED_VARIABLE" in codes


def test_unused_variable_does_not_block_compilation() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Customer asked: {{question}}",
        variables=[
            PromptVariable(name="question", type="string"),
            PromptVariable(name="tone", type="string"),
        ],
    )

    template = PromptCompiler().compile(definition)

    assert template.referenced_variables == ["question"]


def test_malformed_template_is_an_error() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Customer asked: {{question}",
        variables=[PromptVariable(name="question", type="string")],
    )

    report = PromptCompiler().validate(definition)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "MALFORMED_TEMPLATE" in codes


def test_invalid_version_format_is_an_error() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0",
        user_prompt="Hello {{name}}",
        variables=[PromptVariable(name="name", type="string")],
    )

    report = PromptCompiler().validate(definition)

    assert not report.is_valid

    codes = {issue.code for issue in report.errors}

    assert "INVALID_VERSION_FORMAT" in codes


def test_duplicate_variable_references_extracted_once() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="{{context}} then {{question}} then {{context}} again",
        variables=[
            PromptVariable(name="question", type="string"),
            PromptVariable(name="context", type="string"),
        ],
    )

    template = PromptCompiler().compile(definition)

    assert template.referenced_variables == ["context", "question"]


def test_variable_with_optional_whitespace_is_recognized() -> None:

    definition = PromptDefinition(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Question: {{ question }}",
        variables=[PromptVariable(name="question", type="string")],
    )

    report = PromptCompiler().validate(definition)

    assert report.is_valid