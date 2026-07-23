"""
Prompt validation report.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.prompt_engine.validation.prompt_validation_issue import (
    PromptValidationIssue,
)


class PromptValidationReport(BaseModel):
    """
    Result of validating a prompt definition.
    """

    model_config = ConfigDict(frozen=True)

    issues: list[PromptValidationIssue]

    @property
    def errors(self) -> list[PromptValidationIssue]:
        """
        Return only the error-level issues.
        """

        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[PromptValidationIssue]:
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