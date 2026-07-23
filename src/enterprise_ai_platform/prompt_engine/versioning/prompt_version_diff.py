"""
Prompt version diff.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PromptVersionDiff(BaseModel):
    """
    Structured comparison between two versions of the same prompt.
    """

    model_config = ConfigDict(frozen=True)

    name: str

    version_a: str

    version_b: str

    system_prompt_changed: bool

    user_prompt_changed: bool

    added_variables: list[str]

    removed_variables: list[str]

    changed_variables: list[str]

    output_schema_changed: bool

    metadata_changed: bool

    @property
    def has_changes(self) -> bool:
        """
        Return True if anything at all differs between the two
        versions.
        """

        return (
            self.system_prompt_changed
            or self.user_prompt_changed
            or bool(self.added_variables)
            or bool(self.removed_variables)
            or bool(self.changed_variables)
            or self.output_schema_changed
            or self.metadata_changed
        )