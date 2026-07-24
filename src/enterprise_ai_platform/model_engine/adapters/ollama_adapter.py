"""
Ollama model adapter.
"""

from __future__ import annotations

import time
from typing import Iterator

from enterprise_ai_platform.model_engine.adapters.base_model_adapter import (
    BaseModelAdapter,
)
from enterprise_ai_platform.model_engine.models import (
    ModelDefinition,
    ModelRequest,
    ModelResponse,
    StreamChunk,
)


class OllamaAdapter(BaseModelAdapter):
    """
    Adapter for models served by a local Ollama instance.

    No API key required -- Ollama runs entirely locally (or wherever
    `host` points), which is why this is the default provider for V1:
    zero cost, no credentials to manage. Requires the `ollama` Python
    package and an actual Ollama server already running with the
    target model pulled (e.g. `ollama pull llama3.2:3b`).

    The client is constructed lazily on first use (same pattern as
    LocalEmbeddingProvider in the Knowledge Engine), so simply
    registering this adapter never requires Ollama to be installed or
    running -- only actually invoking it does.

    Overrides stream() with genuine incremental token streaming
    (Ollama's client supports stream=True natively), rather than
    relying on BaseModelAdapter's default one-shot fallback -- this is
    the actively-used default provider, so it's the one adapter this
    task gives real streaming to; Anthropic/OpenAI keep the fallback
    for now.
    """

    def __init__(self, host: str = "http://localhost:11434") -> None:

        self._host = host

        self._client = None

    def invoke(
        self,
        request: ModelRequest,
        model: ModelDefinition,
    ) -> ModelResponse:
        """
        Send a chat request to a locally-served Ollama model.
        """

        client = self._get_client()

        messages = self._build_messages(request)

        ollama_model_name = self._resolve_model_name(model)

        start = time.monotonic()

        try:
            response = client.chat(
                model=ollama_model_name,
                messages=messages,
                options=request.parameters,
            )
        except Exception as error:
            raise RuntimeError(
                f"Ollama request failed for model '{ollama_model_name}': "
                f"{error}. Is the Ollama server running at "
                f"'{self._host}' with this model pulled "
                f"(ollama pull {ollama_model_name})?"
            ) from error

        latency = time.monotonic() - start

        return ModelResponse(
            request_id=request.request_id,
            text=response["message"]["content"],
            token_usage={
                "input_tokens": response.get("prompt_eval_count", 0),
                "output_tokens": response.get("eval_count", 0),
            },
            cost=0.0,
            latency_seconds=latency,
        )

    def stream(
        self,
        request: ModelRequest,
        model: ModelDefinition,
    ) -> Iterator[StreamChunk]:
        """
        Stream a chat response from a locally-served Ollama model,
        one incremental text delta at a time.
        """

        client = self._get_client()

        messages = self._build_messages(request)

        ollama_model_name = self._resolve_model_name(model)

        try:
            raw_stream = client.chat(
                model=ollama_model_name,
                messages=messages,
                options=request.parameters,
                stream=True,
            )

            for raw_chunk in raw_stream:

                is_final = raw_chunk.get("done", False)

                yield StreamChunk(
                    request_id=request.request_id,
                    text=raw_chunk["message"]["content"],
                    is_final=is_final,
                    metadata=(
                        {
                            "prompt_eval_count": raw_chunk.get(
                                "prompt_eval_count"
                            ),
                            "eval_count": raw_chunk.get("eval_count"),
                        }
                        if is_final
                        else {}
                    ),
                )

        except Exception as error:
            raise RuntimeError(
                f"Ollama streaming request failed for model "
                f"'{ollama_model_name}': {error}. Is the Ollama server "
                f"running at '{self._host}' with this model pulled?"
            ) from error

    @staticmethod
    def _build_messages(request: ModelRequest) -> list[dict]:

        messages = []

        if request.system_prompt is not None:
            messages.append(
                {"role": "system", "content": request.system_prompt}
            )

        messages.append({"role": "user", "content": request.prompt})

        return messages

    @staticmethod
    def _resolve_model_name(model: ModelDefinition) -> str:

        return model.configuration.get("ollama_model_name", model.name)

    def _get_client(self):
        """
        Lazily construct and cache the Ollama client.
        """

        if self._client is None:

            import ollama

            self._client = ollama.Client(host=self._host)

        return self._client