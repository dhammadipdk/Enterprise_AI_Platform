"""
Provider definition.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ProviderDefinition(BaseModel):
    """
    Describes one registered model provider (Section 9) -- metadata
    about the provider itself, distinct from the BaseModelAdapter
    instance that actually performs invocation.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    description: str | None = None

    metadata: dict[str, Any] = {}