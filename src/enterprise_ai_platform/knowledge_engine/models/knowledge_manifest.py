"""
Knowledge manifest.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class KnowledgeManifest(BaseModel):
    """
    Optional declarative metadata for one knowledge domain.

    A manifest lets a domain author be explicit about ownership,
    description and asset classification instead of relying purely on
    filename-based inference.
    """

    model_config = ConfigDict(frozen=True)

    owner: str | None = None

    description: str | None = None

    version: str | None = None

    tags: list[str] = []

    asset_type_overrides: dict[str, str] = {}