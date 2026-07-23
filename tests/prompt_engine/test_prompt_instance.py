import pytest
from datetime import datetime

from enterprise_ai_platform.prompt_engine import PromptInstance, PromptTemplate


def _template() -> PromptTemplate:

    return PromptTemplate(
        name="explain_zero_dep",
        version="1.0.0",
        user_prompt="Explain: {{question}}",
    )


def test_minimal_instance() -> None:

    instance = PromptInstance(
        template=_template(),
        resolved_variables={"question": "Zero dep matlab kya hai?"},
        rendered_user_prompt="Explain: Zero dep matlab kya hai?",
    )

    assert instance.rendered_system_prompt is None

    assert instance.context is None

    assert isinstance(instance.timestamp, datetime)


def test_timestamp_defaults_automatically() -> None:

    before = datetime.now().astimezone()

    instance = PromptInstance(
        template=_template(),
        resolved_variables={},
        rendered_user_prompt="Explain: hi",
    )

    after = datetime.now().astimezone()

    assert before <= instance.timestamp <= after


def test_is_frozen() -> None:

    instance = PromptInstance(
        template=_template(),
        resolved_variables={},
        rendered_user_prompt="Explain: hi",
    )

    with pytest.raises(Exception):
        instance.rendered_user_prompt = "changed"