"""
Metadata record model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class MetadataRecord(BaseModel):
    """
    Represents one metadata object loaded into the platform.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    source: str

    data: dict[str, Any]