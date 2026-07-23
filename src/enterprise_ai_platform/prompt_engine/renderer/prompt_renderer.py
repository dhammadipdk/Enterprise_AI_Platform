"""
Prompt renderer.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.prompt_engine.models import (
    PromptInstance,
    PromptTemplate,
)
from enterprise_ai_platform.prompt_engine.resolution import (
    VariableResolutionResult,
)
from enterprise_ai_platform.prompt_engine.templating import VARIABLE_PATTERN


class PromptRenderer:
    """
    Renders a compiled PromptTemplate using an already-resolved set of
    variable values, producing an immutable PromptInstance.

    Takes a VariableResolutionResult rather than a plain dict, and
    refuses to render if it contains any error-level issues --
    rendering with an unresolved required variable or a value that
    failed type/rule checking would silently produce a broken prompt,
    so that state is made structurally unreachable rather than relying
    on the caller remembering to check `.is_valid` first.

    Rendering is deterministic (frozen spec, Section 16): the same
    template and the same resolved values always produce the same
    rendered text. `timestamp` on the resulting PromptInstance is
    metadata about when the render happened, not part of the rendered
    text itself, and is the only thing that varies between calls.
    """

    def render(
        self,
        template: PromptTemplate,
        resolution: VariableResolutionResult,
        context: dict[str, Any] | None = None,
    ) -> PromptInstance:
        """
        Render `template` using `resolution`'s resolved values.

        Raises ValueError if `resolution` contains any error-level
        issue.
        """

        if not resolution.is_valid:

            error_messages = "; ".join(
                issue.message for issue in resolution.errors
            )

            raise ValueError(
                f"Cannot render prompt '{template.name}': unresolved "
                f"variable errors: {error_messages}"
            )

        rendered_system_prompt = (
            self._substitute(template.system_prompt, resolution.values)
            if template.system_prompt is not None
            else None
        )

        rendered_user_prompt = self._substitute(
            template.user_prompt,
            resolution.values,
        )

        return PromptInstance(
            template=template,
            resolved_variables=dict(resolution.values),
            rendered_user_prompt=rendered_user_prompt,
            rendered_system_prompt=rendered_system_prompt,
            context=context,
        )

    @staticmethod
    def _substitute(text: str, values: dict[str, Any]) -> str:

        def _replace(match) -> str:

            name = match.group(1)

            if name not in values:
                raise ValueError(
                    f"Template references '{{{{{name}}}}}' but no "
                    f"resolved value was provided for it. Did you "
                    f"forget to run VariableResolver first?"
                )

            value = values[name]

            # A None value represents a legitimately-absent optional
            # variable (VariableResolver's design) -- rendering it as
            # the literal string "None" would look broken in prose,
            # so it becomes an empty string instead.
            return "" if value is None else str(value)

        return VARIABLE_PATTERN.sub(_replace, text)