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
from enterprise_ai_platform.domains.insurance.policy_advisor.location_risk import (
    LocationRiskReference,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.policy_advisor_workflow import (
    POLICY_ADVISOR_WORKFLOW,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.policy_name_resolver import (
    PolicyNameResolver,
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
    ontology_path: Path | str | None = None,
    location_risk_path: Path | str | None = None,
) -> None:
    """
    Wire up everything Policy Advisor needs. All new parameters are
    optional and additive.
    """

    if memory_service is None:
        print(
            "\n" + "=" * 70 + "\n"
            "WARNING: register_policy_advisor_workflow called WITHOUT "
            "memory_service.\n"
            "Conversation facts will NOT persist across turns, and "
            "follow-up questions / compare-by-name will not work "
            "either (both depend on session memory). Pass "
            "memory_service=MemoryService() (created ONCE and reused "
            "across every workflow_service.execute call in this "
            "session).\n" + "=" * 70 + "\n"
        )

    register_policy_advisor_tools(tool_service, catalog_path, ontology_path)

    glossary = (
        JargonGlossary(glossary_path) if glossary_path is not None else None
    )

    location_risk = (
        LocationRiskReference(location_risk_path)
        if location_risk_path is not None
        else None
    )

    policy_name_resolver = PolicyNameResolver(catalog_path)

    workflow_service.register_node_handler(
        NodeType.TASK,
        ensure_session_handler,
    )

    workflow_service.register_node_handler(
        NodeType.MEMORY,
        make_extraction_handler(
            model_service, memory_service, location_risk, policy_name_resolver
        ),
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
        make_tool_node_handler(tool_service, catalog_path, memory_service),
    )

    workflow_service.register_workflow(POLICY_ADVISOR_WORKFLOW)