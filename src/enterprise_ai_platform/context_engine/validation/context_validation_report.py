"""
Context validation report.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.context_engine.validation.context_validation_issue import (
    ContextValidationIssue,
)


class ContextValidationReport(BaseModel):
    """
    Result of validating a set of context fragments before building.
    """

    model_config = ConfigDict(frozen=True)

    issues: list[ContextValidationIssue]

    @property
    def errors(self) -> list[ContextValidationIssue]:
        """
        Return only the error-level issues.
        """

        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ContextValidationIssue]:
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
        """

        return len(self.errors) == 0