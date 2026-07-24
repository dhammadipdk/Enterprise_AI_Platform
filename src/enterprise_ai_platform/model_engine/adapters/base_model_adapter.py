"""
Base model adapter contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from enterprise_ai_platform.model_engine.models import (
    ModelDefinition,
    ModelRequest,
    ModelResponse,
)


class BaseModelAdapter(ABC):
    """
    Base class for all model provider adapters (Section 14).

    Every provider implements this same interface, so switching
    providers never changes application code (Section 2's whole
    vision: Application -> Prompt Engine -> Model Engine -> Provider
    Adapter -> Model). No concrete adapter exists yet in this task --
    this is deliberately the abstraction alone, mirroring how
    BaseEmbeddingProvider and BaseVectorStore in the Knowledge Engine
    were built before any concrete implementation existed for them.
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