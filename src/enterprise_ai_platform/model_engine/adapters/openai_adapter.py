"""
OpenAI model adapter.
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


class OpenAIAdapter(BaseModelAdapter):
    """
    Adapter for the OpenAI API.

    Requires an API key: pass it explicitly via `api_key=`, or set the
    OPENAI_API_KEY environment variable. Registering this adapter
    never requires a key -- only invoking it does.

    Cost is not computed here, same reasoning as AnthropicAdapter:
    per-token pricing changes over time and shouldn't be hardcoded.
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
        Send a chat completion request to the OpenAI API.
        """

        client = self._get_client()

        openai_model_name = model.configuration.get(
            "openai_model_name",
            model.name,
        )

        messages = []

        if request.system_prompt is not None:
            messages.append(
                {"role": "system", "content": request.system_prompt}
            )

        messages.append({"role": "user", "content": request.prompt})

        kwargs: dict = {
            "model": openai_model_name,
            "messages": messages,
        }

        if "temperature" in request.parameters:
            kwargs["temperature"] = request.parameters["temperature"]

        if "max_tokens" in request.parameters:
            kwargs["max_tokens"] = request.parameters["max_tokens"]

        start = time.monotonic()

        try:
            response = client.chat.completions.create(**kwargs)
        except Exception as error:
            raise RuntimeError(
                f"OpenAI request failed for model '{openai_model_name}': "
                f"{error}"
            ) from error

        latency = time.monotonic() - start

        return ModelResponse(
            request_id=request.request_id,
            text=response.choices[0].message.content,
            token_usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            latency_seconds=latency,
        )

    def _get_client(self):
        """
        Lazily construct and cache the OpenAI client.
        """

        if self._client is None:

            key = self._api_key or os.environ.get("OPENAI_API_KEY")

            if not key:
                raise RuntimeError(
                    "No OpenAI API key configured. Pass api_key= to "
                    "OpenAIAdapter(), or set the OPENAI_API_KEY "
                    "environment variable."
                )

            import openai

            self._client = openai.OpenAI(api_key=key)

        return self._client