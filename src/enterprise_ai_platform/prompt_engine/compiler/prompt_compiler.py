"""
Prompt compiler.
"""

from __future__ import annotations

import re

from enterprise_ai_platform.prompt_engine.models import (
    PromptDefinition,
    PromptTemplate,
)
from enterprise_ai_platform.prompt_engine.templating import VARIABLE_PATTERN
from enterprise_ai_platform.prompt_engine.validation import (
    PromptValidationIssue,
    PromptValidationReport,
)

_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


class PromptCompiler:
    """
    Compiles a PromptDefinition into an immutable, render-ready
    PromptTemplate.

    Checks performed (matching the frozen spec's Section 14
    Validation list, where checkable from a definition alone, before
    any runtime render values exist):
      - missing variables: referenced as {{name}} in the prompt text
        but not declared in `variables` (error)
      - unused variables: declared in `variables` but never
        referenced in the prompt text (warning)
      - malformed template syntax: mismatched {{ }} delimiters (error)
      - invalid version format: must be X.Y.Z (error)

    Not yet implemented, deliberately: circular reference checking
    (doesn't apply to the current model -- default_value is a scalar,
    not itself a template) and full output_schema validation (would
    require a new jsonschema dependency for a check nothing currently
    depends on).
    """

    def validate(self, definition: PromptDefinition) -> PromptValidationReport:
        """
        Run all compile-time validation checks against a definition.
        """

        issues: list[PromptValidationIssue] = []

        issues.extend(self._check_version_format(definition))

        issues.extend(self._check_balanced_braces(definition))

        referenced = self._extract_referenced_variables(definition)

        declared_names = {variable.name for variable in definition.variables}

        issues.extend(
            self._check_missing_variables(referenced, declared_names)
        )

        issues.extend(
            self._check_unused_variables(referenced, definition.variables)
        )

        return PromptValidationReport(issues=issues)

    def compile(self, definition: PromptDefinition) -> PromptTemplate:
        """
        Validate and compile a definition into an immutable template.

        Raises ValueError if any error-level validation issue is
        found. Warnings do not block compilation.
        """

        report = self.validate(definition)

        if not report.is_valid:

            error_messages = "; ".join(
                issue.message for issue in report.errors
            )

            raise ValueError(
                f"Cannot compile prompt '{definition.name}': "
                f"{error_messages}"
            )

        referenced = self._extract_referenced_variables(definition)

        return PromptTemplate(
            name=definition.name,
            version=definition.version,
            user_prompt=definition.user_prompt,
            system_prompt=definition.system_prompt,
            variables=definition.variables,
            referenced_variables=referenced,
            output_schema=definition.output_schema,
            metadata=definition.metadata,
        )

    @staticmethod
    def _extract_referenced_variables(
        definition: PromptDefinition,
    ) -> list[str]:

        text = " ".join(
            [definition.system_prompt or "", definition.user_prompt]
        )

        seen: list[str] = []

        for match in VARIABLE_PATTERN.finditer(text):

            name = match.group(1)

            if name not in seen:
                seen.append(name)

        return seen

    @staticmethod
    def _check_balanced_braces(
        definition: PromptDefinition,
    ) -> list[PromptValidationIssue]:

        issues: list[PromptValidationIssue] = []

        fields = (
            ("system_prompt", definition.system_prompt),
            ("user_prompt", definition.user_prompt),
        )

        for label, text in fields:

            if text is None:
                continue

            if text.count("{{") != text.count("}}"):

                issues.append(
                    PromptValidationIssue(
                        severity="error",
                        code="MALFORMED_TEMPLATE",
                        message=(
                            f"'{label}' has mismatched {{{{ }}}} "
                            f"delimiters."
                        ),
                    )
                )

        return issues

    @staticmethod
    def _check_version_format(
        definition: PromptDefinition,
    ) -> list[PromptValidationIssue]:

        if _VERSION_PATTERN.match(definition.version):
            return []

        return [
            PromptValidationIssue(
                severity="error",
                code="INVALID_VERSION_FORMAT",
                message=(
                    f"Version '{definition.version}' does not match "
                    f"the required X.Y.Z format."
                ),
            )
        ]

    @staticmethod
    def _check_missing_variables(
        referenced: list[str],
        declared_names: set[str],
    ) -> list[PromptValidationIssue]:

        missing = [name for name in referenced if name not in declared_names]

        return [
            PromptValidationIssue(
                severity="error",
                code="MISSING_VARIABLE",
                message=(
                    f"Template references '{{{{{name}}}}}' but it is "
                    f"not declared in variables."
                ),
            )
            for name in missing
        ]

    @staticmethod
    def _check_unused_variables(
        referenced: list[str],
        variables,
    ) -> list[PromptValidationIssue]:

        referenced_set = set(referenced)

        unused = [
            variable.name
            for variable in variables
            if variable.name not in referenced_set
        ]

        return [
            PromptValidationIssue(
                severity="warning",
                code="UNUSED_VARIABLE",
                message=(
                    f"Variable '{name}' is declared but never "
                    f"referenced in the template."
                ),
            )
            for name in unused
        ]