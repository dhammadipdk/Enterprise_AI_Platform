"""
Variable resolver.
"""

from __future__ import annotations

import re
from typing import Any

from enterprise_ai_platform.prompt_engine.models import (
    PromptTemplate,
    PromptVariable,
)
from enterprise_ai_platform.prompt_engine.resolution.variable_resolution_issue import (
    VariableResolutionIssue,
)
from enterprise_ai_platform.prompt_engine.resolution.variable_resolution_result import (
    VariableResolutionResult,
)

_TYPE_CHECKS: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "number": (int, float),
    "boolean": bool,
    "list": list,
}


class VariableResolver:
    """
    Resolves a compiled PromptTemplate's declared variables against a
    set of runtime-provided values.

    Responsibilities (the remaining item from the frozen spec's
    Section 14 validation list not already covered by PromptCompiler,
    which only ever sees a definition -- never actual runtime values):
      - unknown variables: a provided value with no matching declared
        variable (warning -- harmless, just ignored downstream)
      - missing required values: a required variable with no provided
        value and no default (error)
      - defaults: an optional variable's declared default_value is
        used when nothing is provided
      - type checking against the variable's declared `type`
      - validation_rules: enum, minimum/maximum (numbers),
        min_length/max_length/pattern (strings) -- a deliberately
        small, concrete subset rather than general JSON Schema.
    """

    def resolve(
        self,
        template: PromptTemplate,
        provided_values: dict[str, Any],
    ) -> VariableResolutionResult:
        """
        Resolve `template`'s declared variables against
        `provided_values`.
        """

        issues: list[VariableResolutionIssue] = []

        declared_names = {variable.name for variable in template.variables}

        issues.extend(
            self._check_unknown_variables(provided_values, declared_names)
        )

        resolved: dict[str, Any] = {}

        for variable in template.variables:

            value, value_issues = self._resolve_one(
                variable,
                provided_values,
            )

            issues.extend(value_issues)

            resolved[variable.name] = value

        return VariableResolutionResult(values=resolved, issues=issues)

    @staticmethod
    def _check_unknown_variables(
        provided_values: dict[str, Any],
        declared_names: set[str],
    ) -> list[VariableResolutionIssue]:

        unknown = [
            key for key in provided_values if key not in declared_names
        ]

        return [
            VariableResolutionIssue(
                severity="warning",
                code="UNKNOWN_VARIABLE",
                message=(
                    f"Value provided for '{key}' but no template "
                    f"variable is declared with that name."
                ),
            )
            for key in unknown
        ]

    def _resolve_one(
        self,
        variable: PromptVariable,
        provided_values: dict[str, Any],
    ) -> tuple[Any, list[VariableResolutionIssue]]:

        if variable.name in provided_values:
            value = provided_values[variable.name]
        elif variable.default_value is not None:
            value = variable.default_value
        elif variable.required:
            return None, [
                VariableResolutionIssue(
                    severity="error",
                    code="MISSING_REQUIRED_VALUE",
                    message=(
                        f"No value provided for required variable "
                        f"'{variable.name}' and it has no default."
                    ),
                )
            ]
        else:
            # Optional, no value provided, no default -- legitimately
            # absent. Skip type/rule checks, which would otherwise
            # spuriously fail against None.
            return None, []

        issues = self._check_type(variable, value)

        issues.extend(self._check_validation_rules(variable, value))

        return value, issues

    @staticmethod
    def _check_type(
        variable: PromptVariable,
        value: Any,
    ) -> list[VariableResolutionIssue]:

        expected = _TYPE_CHECKS.get(variable.type)

        if expected is None:
            # Unknown/custom declared type -- nothing to check against.
            return []

        # bool is a subclass of int in Python, so a plain isinstance
        # check against "number" would silently accept True/False.
        if variable.type == "number" and isinstance(value, bool):
            is_valid = False
        else:
            is_valid = isinstance(value, expected)

        if is_valid:
            return []

        return [
            VariableResolutionIssue(
                severity="error",
                code="TYPE_MISMATCH",
                message=(
                    f"Variable '{variable.name}' expected type "
                    f"'{variable.type}' but got "
                    f"'{type(value).__name__}'."
                ),
            )
        ]

    @staticmethod
    def _check_validation_rules(
        variable: PromptVariable,
        value: Any,
    ) -> list[VariableResolutionIssue]:

        rules = variable.validation_rules

        issues: list[VariableResolutionIssue] = []

        if "enum" in rules and value not in rules["enum"]:
            issues.append(
                VariableResolutionIssue(
                    severity="error",
                    code="INVALID_ENUM_VALUE",
                    message=(
                        f"Variable '{variable.name}' value {value!r} "
                        f"is not one of the allowed values "
                        f"{rules['enum']}."
                    ),
                )
            )

        is_plain_number = isinstance(value, (int, float)) and not isinstance(
            value, bool
        )

        if is_plain_number:

            if "minimum" in rules and value < rules["minimum"]:
                issues.append(
                    VariableResolutionIssue(
                        severity="error",
                        code="VALUE_TOO_LOW",
                        message=(
                            f"Variable '{variable.name}' value {value} "
                            f"is below the minimum of {rules['minimum']}."
                        ),
                    )
                )

            if "maximum" in rules and value > rules["maximum"]:
                issues.append(
                    VariableResolutionIssue(
                        severity="error",
                        code="VALUE_TOO_HIGH",
                        message=(
                            f"Variable '{variable.name}' value {value} "
                            f"is above the maximum of {rules['maximum']}."
                        ),
                    )
                )

        if isinstance(value, str):

            if (
                "min_length" in rules
                and len(value) < rules["min_length"]
            ):
                issues.append(
                    VariableResolutionIssue(
                        severity="error",
                        code="STRING_TOO_SHORT",
                        message=(
                            f"Variable '{variable.name}' is shorter "
                            f"than the minimum length of "
                            f"{rules['min_length']}."
                        ),
                    )
                )

            if (
                "max_length" in rules
                and len(value) > rules["max_length"]
            ):
                issues.append(
                    VariableResolutionIssue(
                        severity="error",
                        code="STRING_TOO_LONG",
                        message=(
                            f"Variable '{variable.name}' is longer "
                            f"than the maximum length of "
                            f"{rules['max_length']}."
                        ),
                    )
                )

            if "pattern" in rules and not re.match(
                rules["pattern"], value
            ):
                issues.append(
                    VariableResolutionIssue(
                        severity="error",
                        code="PATTERN_MISMATCH",
                        message=(
                            f"Variable '{variable.name}' does not "
                            f"match the required pattern "
                            f"'{rules['pattern']}'."
                        ),
                    )
                )

        return issues