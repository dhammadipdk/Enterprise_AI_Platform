"""
Execution unit.
"""

from __future__ import annotations

from typing import Any, Callable

from enterprise_ai_platform.execution_engine.models import ExecutionDefinition


class ExecutionUnit:
    """
    Represents one executable unit (Section 10): a callable plus the
    ExecutionDefinition describing how it should be run.

    Not a pydantic model -- it wraps an arbitrary Python callable,
    which isn't serializable. The callable takes no arguments; bind
    whatever inputs it needs via a closure or functools.partial before
    wrapping it here. Examples from the spec (Workflow Node, Tool
    Call, Prompt Rendering, Model Invocation, Knowledge Lookup, Memory
    Update, Validation) are all naturally expressed this way: e.g.
    `ExecutionUnit(definition, lambda: tool_service.execute(...))`.
    """

    def __init__(
        self,
        definition: ExecutionDefinition,
        func: Callable[[], Any],
    ) -> None:

        self.definition = definition

        self.func = func