"""
Variable resolution result.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.prompt_engine.resolution.variable_resolution_issue import (
    VariableResolutionIssue,
)


class VariableResolutionResult(BaseModel):
    """
    Result of resolving a PromptTemplate's declared variables against
    a set of provided runtime values.

    `values` only ever contains declared template variables (never
    unknown provided keys) and is only meaningful for rendering when
    `is_valid` is True.
    """

    model_config = ConfigDict(frozen=True)

    values: dict[str, Any]

    issues: list[VariableResolutionIssue]

    @property
    def errors(self) -> list[VariableResolutionIssue]:
        """
        Return only the error-level issues.
        """

        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[VariableResolutionIssue]:
        """
        Return only the warning-level issues.
        """

        return [
            issue for issue in self.issues if issue.severity == "warning"
        ]

    @property
    def is_valid(self) -> bool:
        """
        Return True if there are no error-level issues.

        Warnings do not affect validity.
        """

        return len(self.errors) == 0