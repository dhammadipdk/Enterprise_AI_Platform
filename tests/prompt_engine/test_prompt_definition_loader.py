import pytest

from enterprise_ai_platform.prompt_engine import PromptDefinitionLoader


def _valid_data() -> dict:

    return {
        "name": "explain_zero_dep",
        "version": "1.0.0",
        "description": "Explains zero depreciation cover in Hinglish.",
        "system_prompt": (
            "You are InsureAI's explanation assistant. Explain "
            "insurance jargon in simple Hindi/Hinglish for a "
            "first-time buyer."
        ),
        "user_prompt": (
            "Customer asked: {{question}}\n"
            "Retrieved context: {{context}}\n"
            "Explain in simple Hinglish."
        ),
        "variables": [
            {
                "name": "question",
                "type": "string",
                "required": True,
                "description": "The customer's original question.",
            },
            {
                "name": "context",
                "type": "string",
                "required": True,
                "description": "Retrieved policy clause text.",
            },
        ],
        "output_schema": {
            "type": "object",
            "properties": {"explanation": {"type": "string"}},
        },
        "metadata": {"domain": "policy", "persona": "explanation_agent"},
    }


def test_load_full_definition() -> None:

    loader = PromptDefinitionLoader()

    definition = loader.load(_valid_data())

    assert definition.name == "explain_zero_dep"

    assert definition.version == "1.0.0"

    assert len(definition.variables) == 2

    assert definition.variables[0].name == "question"

    assert definition.metadata["persona"] == "explanation_agent"


def test_load_minimal_definition() -> None:

    loader = PromptDefinitionLoader()

    definition = loader.load(
        {
            "name": "minimal_prompt",
            "version": "1.0.0",
            "user_prompt": "Hello {{name}}",
        }
    )

    assert definition.variables == []

    assert definition.description is None


def test_version_coerced_to_string() -> None:

    loader = PromptDefinitionLoader()

    # YAML often parses an unquoted "1.0" as a float; version must
    # still come out as a string.
    definition = loader.load(
        {
            "name": "minimal_prompt",
            "version": 1.0,
            "user_prompt": "Hello {{name}}",
        }
    )

    assert definition.version == "1.0"


def test_missing_name_raises_clear_error() -> None:

    loader = PromptDefinitionLoader()

    data = _valid_data()

    del data["name"]

    with pytest.raises(ValueError, match="name"):
        loader.load(data)


def test_missing_user_prompt_raises_clear_error() -> None:

    loader = PromptDefinitionLoader()

    data = _valid_data()

    del data["user_prompt"]

    with pytest.raises(ValueError, match="user_prompt"):
        loader.load(data)