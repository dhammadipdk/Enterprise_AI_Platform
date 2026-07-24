"""
Structured output enforcer.
"""

from __future__ import annotations

import json
import re
from typing import Any


class StructuredOutputEnforcer:
    """
    Enforces structured (schema-validated JSON) output at the Model
    Engine layer, uniformly across every provider (Section 16: "The
    Prompt Engine requests structured output. The Model Engine
    enforces it.") -- rather than relying on provider-specific native
    mechanisms (OpenAI's response_format, Anthropic's tool-forcing,
    Ollama's format parameter). A provider-native-only approach would
    mean structured output only worked reliably with certain
    providers, breaking Section 2's core promise that changing
    providers never changes application behavior. Provider-native
    modes remain a reasonable future optimization on top of this, not
    a replacement for it.

    Real LLMs frequently don't return pure JSON even when explicitly
    asked -- markdown code fences and conversational preamble/
    postamble around the JSON are the common case, not an edge case --
    so extraction is deliberately lenient about both before falling
    back to a hard failure with the raw text included, so a caller can
    actually see what went wrong.
    """

    _FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)

    def augment_prompt(self, prompt: str, schema: dict[str, Any]) -> str:
        """
        Append explicit JSON-formatting instructions to a prompt.
        """

        schema_text = json.dumps(schema, indent=2)

        return (
            f"{prompt}\n\n"
            f"Respond with ONLY a single JSON value matching this "
            f"schema. Do not include any explanation, markdown "
            f"formatting, or text outside the JSON.\n\n"
            f"Schema:\n{schema_text}"
        )

    def parse_response(self, text: str, schema: dict[str, Any]) -> Any:
        """
        Extract JSON from model output text and validate it against
        `schema`.

        Raises ValueError (with the raw text included) if extraction
        or schema validation fails.
        """

        parsed = self._extract_json(text)

        import jsonschema

        try:
            jsonschema.validate(instance=parsed, schema=schema)
        except jsonschema.ValidationError as error:
            raise ValueError(
                f"Model output did not match the required schema: "
                f"{error.message}. Raw output: {text!r}"
            ) from error

        return parsed

    def _extract_json(self, text: str) -> Any:

        stripped = text.strip()

        fence_match = self._FENCE_PATTERN.search(stripped)

        candidate = fence_match.group(1) if fence_match else stripped

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        for open_char, close_char in (("{", "}"), ("[", "]")):

            start = candidate.find(open_char)

            end = candidate.rfind(close_char)

            if start != -1 and end != -1 and end > start:

                try:
                    return json.loads(candidate[start : end + 1])
                except json.JSONDecodeError:
                    continue

        raise ValueError(
            f"Could not extract valid JSON from model output: {text!r}"
        )