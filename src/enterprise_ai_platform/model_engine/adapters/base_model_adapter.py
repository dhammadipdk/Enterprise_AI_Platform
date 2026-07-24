"""
Base model adapter contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from enterprise_ai_platform.model_engine.models import (
    ModelDefinition,
    ModelRequest,
    ModelResponse,
    StreamChunk,
)


class BaseModelAdapter(ABC):
    """
    Base class for all model provider adapters (Section 14).

    Every provider implements this same interface, so switching
    providers never changes application code (Section 2's whole
    vision: Application -> Prompt Engine -> Model Engine -> Provider
    Adapter -> Model).

    `invoke()` is the only abstract method. `stream()` is deliberately
    concrete with a default fallback (call invoke(), yield the whole
    result as one final chunk) rather than a second abstract method --
    adding an abstract stream() here would have broken every adapter
    already shipped (OllamaAdapter, AnthropicAdapter, OpenAIAdapter),
    since Python won't instantiate a class with an unimplemented
    abstract method. This way every adapter is automatically
    "stream-capable" in a degenerate, non-incremental sense with zero
    changes, and any adapter can override stream() for genuine
    chunk-by-chunk delivery when it's actually implemented.
    """

    @abstractmethod
    def invoke(
        self,
        request: ModelRequest,
        model: ModelDefinition,
    ) -> ModelResponse:
        """
        Send a request to the underlying model and return its
        response.
        """

    def stream(
        self,
        request: ModelRequest,
        model: ModelDefinition,
    ) -> Iterator[StreamChunk]:
        """
        Send a request and yield its response as one or more chunks.

        Default implementation: calls invoke() and yields the entire
        result as a single final chunk. Override this for real
        incremental token/chunk streaming.
        """

        response = self.invoke(request, model)

        yield StreamChunk(
            request_id=response.request_id,
            text=response.text,
            is_final=True,
        )