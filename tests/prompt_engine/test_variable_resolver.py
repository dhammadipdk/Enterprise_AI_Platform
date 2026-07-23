from enterprise_ai_platform.prompt_engine import (
    PromptCompiler,
    PromptDefinition,
    PromptVariable,
    VariableResolver,
)


def _template(variables):

    definition = PromptDefinition(
        name="test_prompt",
        version="1.0.0",
        user_prompt=" ".join(f"{{{{{v.name}}}}}" for v in variables) or "static",
        variables=variables,
    )

    return PromptCompiler().compile(definition)


def test_missing_required_value_is_an_error() -> None:

    template = _template([PromptVariable(name="question", type="string")])

    result = VariableResolver().resolve(template, {})

    assert not result.is_valid

    codes = {issue.code for issue in result.errors}

    assert "MISSING_REQUIRED_VALUE" in codes


def test_default_value_is_applied_when_absent() -> None:

    template = _template(
        [
            PromptVariable(
                name="tone",
                type="string",
                required=False,
                default_value="neutral",
            )
        ]
    )

    result = VariableResolver().resolve(template, {})

    assert result.is_valid

    assert result.values["tone"] == "neutral"


def test_optional_variable_with_no_value_resolves_to_none() -> None:

    template = _template(
        [PromptVariable(name="extra", type="string", required=False)]
    )

    result = VariableResolver().resolve(template, {})

    assert result.is_valid

    assert result.values["extra"] is None


def test_provided_value_overrides_default() -> None:

    template = _template(
        [
            PromptVariable(
                name="tone",
                type="string",
                required=False,
                default_value="neutral",
            )
        ]
    )

    result = VariableResolver().resolve(template, {"tone": "formal"})

    assert result.values["tone"] == "formal"


def test_unknown_provided_variable_is_a_warning() -> None:

    template = _template([PromptVariable(name="question", type="string")])

    result = VariableResolver().resolve(
        template, {"question": "hi", "typo_field": "oops"}
    )

    assert result.is_valid

    codes = {issue.code for issue in result.warnings}

    assert "UNKNOWN_VARIABLE" in codes

    assert "typo_field" not in result.values


def test_bool_is_rejected_as_a_number() -> None:

    template = _template([PromptVariable(name="max_results", type="number")])

    result = VariableResolver().resolve(template, {"max_results": True})

    assert not result.is_valid

    codes = {issue.code for issue in result.errors}

    assert "TYPE_MISMATCH" in codes


def test_valid_number_passes_type_check() -> None:

    template = _template([PromptVariable(name="max_results", type="number")])

    result = VariableResolver().resolve(template, {"max_results": 5})

    assert result.is_valid

    assert result.values["max_results"] == 5


def test_string_type_mismatch() -> None:

    template = _template([PromptVariable(name="question", type="string")])

    result = VariableResolver().resolve(template, {"question": 12345})

    assert not result.is_valid

    codes = {issue.code for issue in result.errors}

    assert "TYPE_MISMATCH" in codes


def test_enum_violation() -> None:

    template = _template(
        [
            PromptVariable(
                name="tone",
                type="string",
                validation_rules={"enum": ["formal", "casual"]},
            )
        ]
    )

    result = VariableResolver().resolve(template, {"tone": "sarcastic"})

    assert not result.is_valid

    codes = {issue.code for issue in result.errors}

    assert "INVALID_ENUM_VALUE" in codes


def test_enum_value_passes() -> None:

    template = _template(
        [
            PromptVariable(
                name="tone",
                type="string",
                validation_rules={"enum": ["formal", "casual"]},
            )
        ]
    )

    result = VariableResolver().resolve(template, {"tone": "formal"})

    assert result.is_valid


def test_number_below_minimum() -> None:

    template = _template(
        [
            PromptVariable(
                name="max_results",
                type="number",
                validation_rules={"minimum": 1, "maximum": 10},
            )
        ]
    )

    result = VariableResolver().resolve(template, {"max_results": 0})

    codes = {issue.code for issue in result.errors}

    assert "VALUE_TOO_LOW" in codes


def test_number_above_maximum() -> None:

    template = _template(
        [
            PromptVariable(
                name="max_results",
                type="number",
                validation_rules={"minimum": 1, "maximum": 10},
            )
        ]
    )

    result = VariableResolver().resolve(template, {"max_results": 50})

    codes = {issue.code for issue in result.errors}

    assert "VALUE_TOO_HIGH" in codes


def test_string_too_short() -> None:

    template = _template(
        [
            PromptVariable(
                name="code",
                type="string",
                validation_rules={"min_length": 3},
            )
        ]
    )

    result = VariableResolver().resolve(template, {"code": "ab"})

    codes = {issue.code for issue in result.errors}

    assert "STRING_TOO_SHORT" in codes


def test_string_too_long() -> None:

    template = _template(
        [
            PromptVariable(
                name="code",
                type="string",
                validation_rules={"max_length": 3},
            )
        ]
    )

    result = VariableResolver().resolve(template, {"code": "abcdef"})

    codes = {issue.code for issue in result.errors}

    assert "STRING_TOO_LONG" in codes


def test_pattern_mismatch() -> None:

    template = _template(
        [
            PromptVariable(
                name="code",
                type="string",
                validation_rules={"pattern": r"^[A-Z]+$"},
            )
        ]
    )

    result = VariableResolver().resolve(template, {"code": "abc"})

    codes = {issue.code for issue in result.errors}

    assert "PATTERN_MISMATCH" in codes


def test_pattern_match_passes() -> None:

    template = _template(
        [
            PromptVariable(
                name="code",
                type="string",
                validation_rules={"pattern": r"^[A-Z]+$"},
            )
        ]
    )

    result = VariableResolver().resolve(template, {"code": "ABC"})

    assert result.is_valid


def test_values_only_contains_declared_variables() -> None:

    template = _template(
        [
            PromptVariable(name="question", type="string"),
            PromptVariable(name="context", type="string"),
        ]
    )

    result = VariableResolver().resolve(
        template,
        {"question": "hi", "context": "policy text", "unrelated": "x"},
    )

    assert set(result.values.keys()) == {"question", "context"}