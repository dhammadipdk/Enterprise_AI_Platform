"""
Node handlers for the Policy Advisor workflow.

Registered per NodeType (not per node) by WorkflowRuntime, so a
single "llm" handler and a single "tool" handler each dispatch
internally based on the node's own `configuration` -- both the
"ask clarifying question" and "format explanation" nodes are the same
NodeType.LLM, and share this one registered handler.
"""

from __future__ import annotations

from typing import Any, Callable

from enterprise_ai_platform.model_engine import ModelService
from enterprise_ai_platform.tool_engine import ToolService
from enterprise_ai_platform.workflow_engine import ExecutionContext, WorkflowNode

from enterprise_ai_platform.domains.insurance.policy_advisor.policy_advisor_workflow import (
    REQUIRED_SLOTS,
)


def check_required_slots_handler(
    node: WorkflowNode,
    context: ExecutionContext,
) -> dict[str, Any]:
    """
    Decision handler: checks whether every slot recommend_policies
    needs is present in context, and stashes which ones are missing
    (as metadata, for the clarifying-question prompt to read) --
    metadata rather than a declared output, since downstream edges
    don't need to branch on the missing-slot *list*, only on whether
    the info is complete.
    """

    missing = [
        slot for slot in REQUIRED_SLOTS if context.get_variable(slot) is None
    ]

    has_required_info = len(missing) == 0

    context.set_metadata("missing_slots", missing)

    return {
        "has_required_info": has_required_info,
        "missing_required_info": not has_required_info,
    }


def make_llm_node_handler(
    model_service: ModelService,
    model_name: str = "explanation_model",
) -> Callable[[WorkflowNode, ExecutionContext], dict[str, Any]]:
    """
    Build the shared LLM-node handler, closing over the ModelService
    to call (the injected-callable pattern used throughout this
    codebase, e.g. GraphBuilder/HybridRetriever).
    """

    def _ask_clarifying_question(context: ExecutionContext) -> str:

        missing_slots = context.get_metadata("missing_slots", [])

        return (
            "Customer wants motor insurance advice on WhatsApp. We "
            f"still need: {', '.join(missing_slots)}. Ask ONE short, "
            "friendly question in Hinglish (Hindi+English WhatsApp "
            "style) to get this missing information. Do not ask for "
            "anything else, and do not repeat information already "
            "known."
        )

    def _format_explanation(context: ExecutionContext) -> str:

        recommendations_result = context.get_variable(
            "recommendations_result",
            {},
        )

        recommendations = recommendations_result.get("recommendations", [])

        if not recommendations:
            message = recommendations_result.get(
                "message",
                "No matching policies were found.",
            )
            return (
                f"Explain this to the customer warmly, in Hinglish "
                f"(Hindi+English WhatsApp style): {message}"
            )

        top = recommendations[0]

        why_not_cheapest = recommendations_result.get("why_not_cheapest")

        prompt = (
            "Explain this insurance recommendation to a customer in "
            "Hinglish (Hindi+English WhatsApp style) -- warm, simple, "
            "and explain any jargon (like 'zero dep' or 'NCB') rather "
            "than assuming they know it:\n"
            f"Top pick: {top['product_name']} by {top['insurer_name']}\n"
            f"Estimated annual premium: Rs {top['estimated_annual_premium_rs']}\n"
            f"Why it fits: {top['plain_language_pitch']}\n"
            f"Best for: {top['best_for']}\n"
        )

        if why_not_cheapest:
            prompt += (
                f"If it seems relevant, briefly mention: "
                f"{why_not_cheapest}\n"
            )

        return prompt

    def llm_node_handler(
        node: WorkflowNode,
        context: ExecutionContext,
    ) -> dict[str, Any]:

        prompt_kind = node.configuration.get("prompt_kind")

        if prompt_kind == "ask_clarifying_question":
            prompt = _ask_clarifying_question(context)
        elif prompt_kind == "format_explanation":
            prompt = _format_explanation(context)
        else:
            raise ValueError(
                f"Unknown prompt_kind '{prompt_kind}' for LLM node "
                f"'{node.id}'."
            )

        response = model_service.execute(model_name, prompt)

        return {"response_text": response.text}

    return llm_node_handler


def make_tool_node_handler(
    tool_service: ToolService,
) -> Callable[[WorkflowNode, ExecutionContext], dict[str, Any]]:
    """
    Build the shared Tool-node handler.
    """

    def tool_node_handler(
        node: WorkflowNode,
        context: ExecutionContext,
    ) -> dict[str, Any]:

        tool_name = node.configuration.get("tool_name")

        if tool_name != "recommend_policies":
            raise ValueError(
                f"Unknown tool_name '{tool_name}' for Tool node "
                f"'{node.id}'."
            )

        parameters = {
            "vehicle_idv_rs": context.get_variable("vehicle_idv_rs"),
            "vehicle_age_years": context.get_variable("vehicle_age_years"),
            "ncb_percent": context.get_variable("ncb_percent", 0),
            "ev_flag": context.get_variable("ev_flag", False),
            "coverage_priorities": context.get_variable(
                "coverage_priorities",
                [],
            ),
            "budget_sensitivity_1to5": context.get_variable(
                "budget_sensitivity_1to5",
                3,
            ),
            "prefers_cashless": context.get_variable(
                "prefers_cashless",
                False,
            ),
        }

        # Omit budget_cap_rs entirely when unset, rather than passing
        # None -- the input_schema declares it as {"type": "number"},
        # not nullable, so an explicit None fails schema validation
        # even though it's semantically "no cap". Omitting the key
        # lets PolicyRecommendationEngine's own default (None) apply
        # instead, without ever handing a null to the validator.
        budget_cap_rs = context.get_variable("budget_cap_rs")

        if budget_cap_rs is not None:
            parameters["budget_cap_rs"] = budget_cap_rs

        response = tool_service.execute(
            "recommend_policies",
            parameters=parameters,
        )

        if response.status == "failure":
            raise RuntimeError(
                f"recommend_policies tool failed: {response.error}"
            )

        return {"recommendations_result": response.result}

    return tool_node_handler