import pytest

from enterprise_ai_platform.model_engine.structured_output import (
    StructuredOutputEnforcer,
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "explanation": {"type": "string"},
    },
    "required": ["explanation"],
}


def test_augment_prompt_includes_schema_and_instructions() -> None:

    enforcer = StructuredOutputEnforcer()

    augmented = enforcer.augment_prompt("Zero dep matlab kya hai?", _SCHEMA)

    assert "Zero dep matlab kya hai?" in augmented

    assert "JSON" in augmented

    assert '"explanation"' in augmented


def test_parse_response_clean_json() -> None:

    enforcer = StructuredOutputEnforcer()

    result = enforcer.parse_response(
        '{"explanation": "Zero dep covers full part cost."}', _SCHEMA
    )

    assert result == {"explanation": "Zero dep covers full part cost."}


def test_parse_response_markdown_fenced_with_json_tag() -> None:

    enforcer = StructuredOutputEnforcer()

    result = enforcer.parse_response(
        '```json\n{"explanation": "hi"}\n```', _SCHEMA
    )

    assert result == {"explanation": "hi"}


def test_parse_response_markdown_fenced_without_tag() -> None:

    enforcer = StructuredOutputEnforcer()

    result = enforcer.parse_response('```\n{"explanation": "hi"}\n```', _SCHEMA)

    assert result == {"explanation": "hi"}


def test_parse_response_with_conversational_preamble() -> None:

    enforcer = StructuredOutputEnforcer()

    result = enforcer.parse_response(
        'Here is the response:\n{"explanation": "hi"}', _SCHEMA
    )

    assert result == {"explanation": "hi"}


def test_parse_response_with_preamble_and_postamble() -> None:

    enforcer = StructuredOutputEnforcer()

    result = enforcer.parse_response(
        'Sure! {"explanation": "hi"} Let me know if you need more.',
        _SCHEMA,
    )

    assert result == {"explanation": "hi"}


def test_parse_response_array_schema() -> None:

    enforcer = StructuredOutputEnforcer()

    array_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"term": {"type": "string"}},
            "required": ["term"],
        },
    }

    result = enforcer.parse_response(
        '[{"term": "IDV"}, {"term": "NCB"}]', array_schema
    )

    assert result == [{"term": "IDV"}, {"term": "NCB"}]


def test_parse_response_no_json_present_raises() -> None:

    enforcer = StructuredOutputEnforcer()

    with pytest.raises(ValueError, match="Could not extract valid JSON"):
        enforcer.parse_response("I cannot help with that request.", _SCHEMA)


def test_parse_response_valid_json_wrong_schema_raises() -> None:

    enforcer = StructuredOutputEnforcer()

    with pytest.raises(ValueError, match="did not match the required schema"):
        # Missing the required "explanation" key.
        enforcer.parse_response('{"wrong_key": "hi"}', _SCHEMA)


def test_parse_response_wrong_type_raises() -> None:

    enforcer = StructuredOutputEnforcer()

    with pytest.raises(ValueError, match="did not match the required schema"):
        # explanation must be a string, not a number.
        enforcer.parse_response('{"explanation": 42}', _SCHEMA)


def test_parse_response_nested_braces_in_string_values() -> None:

    enforcer = StructuredOutputEnforcer()

    schema = {
        "type": "object",
        "properties": {"outer": {"type": "object"}},
    }

    result = enforcer.parse_response(
        '{"outer": {"inner": "value with { brace } inside"}}', schema
    )

    assert result == {"outer": {"inner": "value with { brace } inside"}}