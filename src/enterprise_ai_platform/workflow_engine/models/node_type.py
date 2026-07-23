"""
Workflow node type.
"""

from __future__ import annotations

from enum import Enum


class NodeType(str, Enum):
    """
    Every node type the frozen spec (Section 10) names as supported.

    Start / End / Task / Decision / Wait get real execution behavior
    starting with the Execution task. LLM / Tool / Knowledge / Memory
    / Human Approval / Parallel / Loop / Custom are represented here
    for spec-completeness, but have no execution handler yet -- each
    depends on an engine (Model, Tool, Memory, Agent Runtime) that
    doesn't exist yet. Attempting to execute one of those will raise a
    clear "no handler registered" error rather than silently no-oping.
    """

    START = "start"

    END = "end"

    TASK = "task"

    LLM = "llm"

    TOOL = "tool"

    KNOWLEDGE = "knowledge"

    DECISION = "decision"

    PARALLEL = "parallel"

    LOOP = "loop"

    WAIT = "wait"

    HUMAN_APPROVAL = "human_approval"

    MEMORY = "memory"

    CUSTOM = "custom"