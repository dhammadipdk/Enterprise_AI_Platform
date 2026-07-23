"""
Prompt definition loader.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.prompt_engine.models.prompt_definition import (
    PromptDefinition,
)
from enterprise_ai_platform.prompt_engine.models.prompt_variable import (
    PromptVariable,
)


class PromptDefinitionLoader:
    """
    Builds a PromptDefinition from raw parsed data (typically a dict
    parsed from a YAML prompt asset via
    KnowledgeService.load_asset_content, since prompts are stored
    inside the Knowledge Repository).
    """

    def load(self, data: dict[str, Any]) -> PromptDefinition:
        """
        Build a PromptDefinition from a raw dict.
        """

        try:

            variables = [
                PromptVariable(**variable_data)
                for variable_data in data.get("variables", [])
            ]

            return PromptDefinition(
                name=data["name"],
                version=str(data["version"]),
                user_prompt=data["user_prompt"],
                description=data.get("description"),
                system_prompt=data.get("system_prompt"),
                variables=variables,
                output_schema=data.get("output_schema"),
                metadata=data.get("metadata", {}),
            )

        except KeyError as error:
            raise ValueError(
                f"Prompt definition is missing a required field: "
                f"{error}. Required fields: name, version, user_prompt."
            ) from error