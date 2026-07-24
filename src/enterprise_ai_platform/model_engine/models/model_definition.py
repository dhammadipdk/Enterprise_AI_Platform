"""
Model definition.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.model_engine.models.model_capability import (
    ModelCapability,
)


class ModelDefinition(BaseModel):
    """
    Describes one model as a managed runtime resource (Section 1),
    not an API client -- application code addresses a model by name,
    never a specific provider's SDK.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    version: str

    provider: str

    family: str | None = None

    capabilities: list[ModelCapability] = []

    limits: dict[str, Any] = {}

    configuration: dict[str, Any] = {}

    metadata: dict[str, Any] = {}