"""
Validation report.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.knowledge_engine.validation.validation_issue import (
    ValidationIssue,
)


class ValidationReport(BaseModel):
    """
    Result of validating a knowledge repository.
    """

    model_config = ConfigDict(frozen=True)

    issues: list[ValidationIssue]

    @property
    def errors(self) -> list[ValidationIssue]:
        """
        Return only the error-level issues.
        """

        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
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