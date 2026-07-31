"""
Thin execution wrapper that logs each Policy Advisor conversation turn.
"""

from __future__ import annotations

from typing import Any

from enterprise_ai_platform.workflow_engine import WorkflowInstance, WorkflowService

from enterprise_ai_platform.domains.insurance.policy_advisor.conversation_logger import (
    ConversationLogger,
)


def execute_policy_advisor_with_logging(
    workflow_service: WorkflowService,
    conversation_logger: ConversationLogger,
    initial_variables: dict[str, Any],
) -> WorkflowInstance:
    """
    Runs the policy_advisor workflow, then logs the turn -- logging
    is a cross-cutting concern, kept outside the workflow graph
    itself rather than adding a dedicated node for it.
    """

    instance = workflow_service.execute(
        "policy_advisor",
        initial_variables=initial_variables,
    )

    session_id = instance.context.get_variable("session_id")

    outcome_path = [result.node_id for result in instance.node_history]

    response_text = instance.context.get_variable("response_text")

    extracted_name = instance.context.get_metadata(
        "extracted_name_for_redaction"
    )

    conversation_logger.log_turn(
        session_id=session_id,
        input_variables=initial_variables,
        outcome_path=outcome_path,
        response_text=response_text,
        raw_customer_message=initial_variables.get("customer_message"),
        extracted_name=extracted_name,
    )

    return instance