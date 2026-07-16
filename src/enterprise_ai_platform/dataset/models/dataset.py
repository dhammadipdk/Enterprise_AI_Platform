"""
Dataset model.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Dataset(BaseModel):
    """
    Represents a dataset loaded into the platform.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    records: list[dict[str, Any]]