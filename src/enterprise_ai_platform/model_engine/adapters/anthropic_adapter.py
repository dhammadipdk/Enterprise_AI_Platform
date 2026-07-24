"""
Anthropic model adapter.
"""

from __future__ import annotations

import os
import time

from enterprise_ai_platform.model_engine.adapters.base_model_adapter import (
    BaseModelAdapter,
)
from enterprise_ai_platform.model_engine.models import (
    ModelDefinition,
    ModelRequest,
    ModelResponse,
)


class AnthropicAdapter(BaseModelAdapter):
    """
    Adapter for the Anthropic API.

    Requires an API key: pass it explicitly via `api_key=`, or set the
    ANTHROPIC_API_KEY environment variable. Registering this adapter
    never requires a key -- only invoking it does, and the error
    message is explicit about what's missing rather than surfacing a
    raw SDK exception.

    Cost is not computed here (left as None on the response) --
    per-token pricing changes over time, and hardcoding a pricing
    table now risks it silently going stale. Real cost tracking
    (Section 20) is a reasonable dedicated future task.
    """

    def __init__(self, api_key: str | None = None) -> None:

        self._api_key = api_key

        self._client = None

    def invoke(
        self,
        request: ModelRequest,
        model: ModelDefinition,
    ) -> ModelResponse:
        """
        Send a message request to the Anthropic API.
        """

        client = self._get_client()

        anthropic_model_name = model.configuration.get(
            "anthropic_model_name",
            model.name,
        )

        kwargs: dict = {
            "model": anthropic_model_name,
            "max_tokens": request.parameters.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": request.prompt}],
        }

        if request.system_prompt is not None:
            kwargs["system"] = request.system_prompt

        if "temperature" in request.parameters:
            kwargs["temperature"] = request.parameters["temperature"]

        start = time.monotonic()

        try:
            response = client.messages.create(**kwargs)
        except Exception as error:
            raise RuntimeError(
                f"Anthropic request failed for model "
                f"'{anthropic_model_name}': {error}"
            ) from error

        latency = time.monotonic() - start

        text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        return ModelResponse(
            request_id=request.request_id,
            text=text,
            token_usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            latency_seconds=latency,
        )

    def _get_client(self):
        """
        Lazily construct and cache the Anthropic client.
        """

        if self._client is None:

            key = self._api_key or os.environ.get("ANTHROPIC_API_KEY")

            if not key:
                raise RuntimeError(
                    "No Anthropic API key configured. Pass api_key= to "
                    "AnthropicAdapter(), or set the ANTHROPIC_API_KEY "
                    "environment variable."
                )

            import anthropic

            self._client = anthropic.Anthropic(api_key=key)

        return self._client