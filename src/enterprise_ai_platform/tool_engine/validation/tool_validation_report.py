"""
Tool validation report.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.tool_engine.validation.tool_validation_issue import (
    ToolValidationIssue,
)


class ToolValidationReport(BaseModel):
    """
    Result of validating parameters against a tool's input schema.
    """

    model_config = ConfigDict(frozen=True)

    issues: list[ToolValidationIssue]

    @property
    def errors(self) -> list[ToolValidationIssue]:
        """
        Return only the error-level issues.
        """

        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ToolValidationIssue]:
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