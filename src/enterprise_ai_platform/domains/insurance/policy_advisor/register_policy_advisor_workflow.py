"""
Registers the Policy Advisor workflow and its node handlers.
"""

from __future__ import annotations

from pathlib import Path

from enterprise_ai_platform.model_engine import ModelService
from enterprise_ai_platform.tool_engine import ToolService
from enterprise_ai_platform.workflow_engine import NodeType, WorkflowService

from enterprise_ai_platform.domains.insurance.policy_advisor.handlers import (
    check_required_slots_handler,
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
) -> None:
    """
    Wire up everything Policy Advisor needs: the recommend_policies
    tool, the workflow definition, and its node handlers.
    """

    register_policy_advisor_tools(tool_service, catalog_path)

    workflow_service.register_node_handler(
        NodeType.DECISION,
        check_required_slots_handler,
    )

    workflow_service.register_node_handler(
        NodeType.LLM,
        make_llm_node_handler(model_service),
    )

    workflow_service.register_node_handler(
        NodeType.TOOL,
        make_tool_node_handler(tool_service),
    )

    workflow_service.register_workflow(POLICY_ADVISOR_WORKFLOW)
