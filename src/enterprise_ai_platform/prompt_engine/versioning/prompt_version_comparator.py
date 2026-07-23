"""
Prompt version comparator.
"""

from __future__ import annotations

from enterprise_ai_platform.prompt_engine.models import PromptTemplate
from enterprise_ai_platform.prompt_engine.versioning.prompt_version_diff import (
    PromptVersionDiff,
)


class PromptVersionComparator:
    """
    Compares two compiled versions of the same prompt and reports what
    changed.

    A pure function of two PromptTemplate objects -- no registry or
    service dependency, independently testable like PromptCompiler,
    VariableResolver and PromptRenderer.
    """

    def compare(
        self,
        template_a: PromptTemplate,
        template_b: PromptTemplate,
    ) -> PromptVersionDiff:
        """
        Compare two versions of the same prompt.

        Raises ValueError if the two templates have different names
        (comparing versions of different prompts isn't meaningful).
        """

        if template_a.name != template_b.name:
            raise ValueError(
                f"Cannot compare versions of different prompts: "
                f"'{template_a.name}' vs '{template_b.name}'."
            )

        variables_a = {
            variable.name: variable for variable in template_a.variables
        }

        variables_b = {
            variable.name: variable for variable in template_b.variables
        }

        added = sorted(set(variables_b) - set(variables_a))

        removed = sorted(set(variables_a) - set(variables_b))

        common = set(variables_a) & set(variables_b)

        changed = sorted(
            name
            for name in common
            if variables_a[name] != variables_b[name]
        )

        return PromptVersionDiff(
            name=template_a.name,
            version_a=template_a.version,
            version_b=template_b.version,
            system_prompt_changed=(
                template_a.system_prompt != template_b.system_prompt
            ),
            user_prompt_changed=(
                template_a.user_prompt != template_b.user_prompt
            ),
            added_variables=added,
            removed_variables=removed,
            changed_variables=changed,
            output_schema_changed=(
                template_a.output_schema != template_b.output_schema
            ),
            metadata_changed=(
                template_a.metadata != template_b.metadata
            ),
        )