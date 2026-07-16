"""
Metadata subsystem.
"""

from enterprise_ai_platform.metadata.metadata_registry import (
    MetadataRegistry,
)
from enterprise_ai_platform.metadata.models import MetadataRecord

__all__ = [
    "MetadataRecord",
    "MetadataRegistry",
]