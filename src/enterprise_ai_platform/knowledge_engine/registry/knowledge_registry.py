"""
Knowledge registry.
"""

from enterprise_ai_platform.framework.base import BaseRegistry
from enterprise_ai_platform.knowledge_engine.models import (
    KnowledgeRepository,
)


class KnowledgeRegistry(
    BaseRegistry[KnowledgeRepository]
):
    """
    Registry of knowledge repositories.
    """

    pass