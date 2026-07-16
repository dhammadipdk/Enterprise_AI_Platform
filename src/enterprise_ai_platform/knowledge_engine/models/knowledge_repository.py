"""
Knowledge repository.
"""

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.knowledge_engine.models.knowledge_domain import (
    KnowledgeDomain,
)


class KnowledgeRepository(BaseModel):
    """
    Entire knowledge repository.
    """

    model_config = ConfigDict(frozen=True)

    domains: list[KnowledgeDomain]