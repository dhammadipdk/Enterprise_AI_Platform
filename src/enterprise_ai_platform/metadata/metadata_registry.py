"""
Metadata registry.
"""

from enterprise_ai_platform.framework.base import BaseRegistry
from enterprise_ai_platform.metadata.models import MetadataRecord


class MetadataRegistry(BaseRegistry[MetadataRecord]):
    """
    Stores platform metadata records.
    """

    pass