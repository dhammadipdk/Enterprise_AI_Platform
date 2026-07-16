"""
Metadata subsystem.
"""

from enterprise_ai_platform.metadata.metadata_registry import (
    MetadataRegistry,
)
from enterprise_ai_platform.metadata.models import MetadataRecord
from enterprise_ai_platform.metadata.providers import CSVProvider

__all__ = [
    "MetadataRecord",
    "MetadataRegistry",
    "CSVProvider",
]