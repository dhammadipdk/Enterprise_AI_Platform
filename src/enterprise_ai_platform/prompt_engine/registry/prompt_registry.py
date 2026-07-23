"""
Prompt registry.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base import BaseRegistry
from enterprise_ai_platform.prompt_engine.models import PromptTemplate


class PromptRegistry(BaseRegistry[PromptTemplate]):
    """
    Registry of compiled prompt templates, keyed by "name@version".
    """

    pass