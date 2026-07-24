"""
Workflow validation report.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from enterprise_ai_platform.workflow_engine.validation.workflow_validation_issue import (
    WorkflowValidationIssue,
)


class WorkflowValidationReport(BaseModel):
    """
    Result of validating a workflow definition.
    """

    model_config = ConfigDict(frozen=True)

    issues: list[WorkflowValidationIssue]

    @property
    def errors(self) -> list[WorkflowValidationIssue]:
        """
        Return only the error-level issues.
        """

        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[WorkflowValidationIssue]:
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