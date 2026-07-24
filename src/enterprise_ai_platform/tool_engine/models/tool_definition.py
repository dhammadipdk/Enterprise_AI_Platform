"""
Tool definition.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.tool_engine.models.tool_category import (
    ToolCategory,
)
from enterprise_ai_platform.tool_engine.models.tool_permission import (
    ToolPermission,
)


class ToolDefinition(BaseModel):
    """
    Describes one tool as a reusable enterprise capability (Section
    1), not a specific external system -- applications never invoke
    external systems directly, only through the Tool Engine.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    version: str

    description: str | None = None

    category: ToolCategory = ToolCategory.CUSTOM

    input_schema: dict[str, Any] | None = None

    output_schema: dict[str, Any] | None = None

    configuration: dict[str, Any] = {}

    permissions: list[ToolPermission] = []

    owner: str | None = None

    metadata: dict[str, Any] = {}