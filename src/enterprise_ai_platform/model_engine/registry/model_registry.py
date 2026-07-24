"""
Model registry.
"""

from __future__ import annotations

from enterprise_ai_platform.framework.base import BaseRegistry
from enterprise_ai_platform.model_engine.models import ModelDefinition


class ModelRegistry(BaseRegistry[ModelDefinition]):
    """
    Registry of registered model definitions, keyed by "name@version".
    """

    pass