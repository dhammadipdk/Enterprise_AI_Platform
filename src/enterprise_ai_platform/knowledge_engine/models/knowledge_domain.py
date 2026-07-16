"""
Knowledge domain.
"""

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.knowledge_engine.models.knowledge_asset import (
    KnowledgeAsset,
)


class KnowledgeDomain(BaseModel):
    """
    Represents one knowledge domain.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    assets: list[KnowledgeAsset]