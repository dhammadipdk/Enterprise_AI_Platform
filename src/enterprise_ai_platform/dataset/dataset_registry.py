"""
Dataset registry.
"""

from enterprise_ai_platform.dataset.models import Dataset
from enterprise_ai_platform.framework.base import BaseRegistry


class DatasetRegistry(BaseRegistry[Dataset]):
    """
    Registry for datasets.
    """

    pass