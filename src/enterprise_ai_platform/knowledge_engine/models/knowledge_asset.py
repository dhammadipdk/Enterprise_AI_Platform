"""
Knowledge asset.
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class KnowledgeAsset(BaseModel):
    """
    Represents one knowledge asset.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    asset_type: str

    path: Path