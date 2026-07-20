"""
Knowledge provider registry.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base import BaseProvider, BaseRegistry


class KnowledgeProviderRegistry(BaseRegistry[BaseProvider]):
    """
    Registry of knowledge providers, keyed by file extension
    (for example ".csv", ".md").
    """

    pass