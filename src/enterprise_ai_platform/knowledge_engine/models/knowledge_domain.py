"""
Knowledge domain.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.knowledge_engine.models.knowledge_asset import (
    KnowledgeAsset,
)
from enterprise_ai_platform.knowledge_engine.models.knowledge_manifest import (
    KnowledgeManifest,
)


class KnowledgeDomain(BaseModel):
    """
    Represents one knowledge domain.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    assets: list[KnowledgeAsset]

    manifest: KnowledgeManifest | None = None