"""
Registers the Policy Advisor workflow and its node handlers.
"""

from __future__ import annotations

from pathlib import Path

from enterprise_ai_platform.knowledge_engine import KnowledgeService
from enterprise_ai_platform.memory_engine import MemoryService
from enterprise_ai_platform.model_engine import ModelService
from enterprise_ai_platform.tool_engine import ToolService
from enterprise_ai_platform.workflow_engine import NodeType, WorkflowService

from enterprise_ai_platform.domains.insurance.policy_advisor.glossary import (
    JargonGlossary,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.handlers import (
    check_required_slots_handler,
    ensure_session_handler,
    make_extraction_handler,
    make_llm_node_handler,
    make_tool_node_handler,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.policy_advisor_workflow import (
    POLICY_ADVISOR_WORKFLOW,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.tools import (
    register_policy_advisor_tools,
)


def register_policy_advisor_workflow(
    workflow_service: WorkflowService,
    tool_service: ToolService,
    model_service: ModelService,
    catalog_path: Path | str,
    knowledge_service: KnowledgeService | None = None,
    glossary_path: Path | str | None = None,
    memory_service: MemoryService | None = None,
) -> None:
    """
    Wire up everything Policy Advisor needs.

    `memory_service` (optional, additive) enables free-text profile
    extraction and cross-turn session memory. Without it, the
    extraction node still runs but has no prior facts to load and
    nothing is persisted -- callers must keep supplying structured
    kwargs directly, exactly as before.
    """

    register_policy_advisor_tools(tool_service, catalog_path)

    glossary = (
        JargonGlossary(glossary_path) if glossary_path is not None else None
    )

    workflow_service.register_node_handler(
        NodeType.TASK,
        ensure_session_handler,
    )

    workflow_service.register_node_handler(
        NodeType.MEMORY,
        make_extraction_handler(model_service, memory_service),
    )

    workflow_service.register_node_handler(
        NodeType.DECISION,
        check_required_slots_handler,
    )

    workflow_service.register_node_handler(
        NodeType.LLM,
        make_llm_node_handler(model_service, knowledge_service, glossary),
    )

    workflow_service.register_node_handler(
        NodeType.TOOL,
        make_tool_node_handler(tool_service),
    )

    workflow_service.register_workflow(POLICY_ADVISOR_WORKFLOW)