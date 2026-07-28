"""
Node handlers for the Policy Advisor workflow.

Registered per NodeType (not per node) by WorkflowRuntime, so a
single "llm" handler and a single "tool" handler each dispatch
internally based on the node's own `configuration`.
"""

from __future__ import annotations

from typing import Any, Callable

from enterprise_ai_platform.model_engine import ModelService
from enterprise_ai_platform.tool_engine import ToolService
from enterprise_ai_platform.workflow_engine import ExecutionContext, WorkflowNode

from enterprise_ai_platform.domains.insurance.policy_advisor.policy_advisor_workflow import (
    REQUIRED_SLOTS,
)

_RANK_LABELS = ["Best match", "2nd best match", "3rd best match"]


def check_required_slots_handler(
    node: WorkflowNode,
    context: ExecutionContext,
) -> dict[str, Any]:
    """
    Decision handler: checks whether the profile info both
    recommend_policies and compare_policies need is present, AND
    determines whether this is a comparison request (both policy_id_a
    and policy_id_b named) or a recommendation request.

    Produces three mutually exclusive flags rather than two
    independent booleans -- WorkflowRuntime's edge conditions only
    check ONE named variable's truthiness each (no compound AND/OR
    expressions), so each routing outcome needs its own single flag
    that is True in exactly the cases that should take that edge.

    Naming both policies without also giving vehicle info still
    routes to the clarifying question, not straight to comparison --
    compare_policies needs vehicle_idv_rs/vehicle_age_years too, so
    "missing info" is checked before "which mode", not after.
    """

    missing = [
        slot for slot in REQUIRED_SLOTS if context.get_variable(slot) is None
    ]

    has_required_info = len(missing) == 0

    context.set_metadata("missing_slots", missing)

    is_comparison_request = (
        context.get_variable("policy_id_a") is not None
        and context.get_variable("policy_id_b") is not None
    )

    return {
        "should_ask_clarifying": not has_required_info,
        "should_compare": has_required_info and is_comparison_request,
        "should_recommend": has_required_info and not is_comparison_request,
    }


def make_llm_node_handler(
    model_service: ModelService,
    knowledge_service: Any | None = None,
    glossary: Any | None = None,
    model_name: str = "explanation_model",
) -> Callable[[WorkflowNode, ExecutionContext], dict[str, Any]]:
    """
    Build the shared LLM-node handler, closing over the ModelService
    (and optionally KnowledgeService / JargonGlossary) to call.
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

    def _regulatory_requirement() -> str | None:
        """
        Retrieve the IRDAI plain-language disclosure requirement from
        the real regulatory_knowledge corpus. Degrades silently to
        None if knowledge_service isn't configured or retrieval fails
        for any reason -- an enhancement, not something that should
        take down the whole response.
        """

        if knowledge_service is None:
            return None

        try:
            matches = knowledge_service.hybrid_search(
                "insurance",
                "plain language recommendation exclusions disclosure",
                top_k=1,
                domain="regulatory_knowledge",
            )
        except Exception:
            return None

        if not matches:
            return None

        return matches[0].chunk.metadata.get("implication_for_agent")

    def _regulatory_guardrail_text(regulatory_note: str | None) -> str:

        if not regulatory_note:
            return ""

        return (
            f"\n\nRegulatory requirement you must also satisfy in "
            f"your message: {regulatory_note}\n"
            f"IMPORTANT: only mention specific details (charges, "
            f"discontinuance terms, risks) if they were explicitly "
            f"given to you above. If this requirement mentions "
            f"something you have no specific facts about, say that "
            f"details are available on request -- do NOT invent "
            f"specific claims like penalty amounts or terms you were "
            f"not given."
        )

    def _glossary_guardrail_text(glossary_facts: list[str]) -> str:

        if glossary_facts:
            return (
                "\n\nIf you mention any of these terms, use EXACTLY "
                "this meaning -- do not substitute your own "
                "understanding of the term, even if you think you "
                "know it:\n"
                + "\n".join(f"- {fact}" for fact in glossary_facts)
            )

        return (
            "\n\nOnly explain jargon terms if you are certain of "
            "their correct meaning; otherwise mention the term name "
            "without defining it."
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

        facts: list[str] = []

        all_matched_coverage: set[str] = set()

        common_coverage = set(recommendations[0].get("matched_coverage", []))

        for rec in recommendations[1:]:
            common_coverage &= set(rec.get("matched_coverage", []))

        for i, rec in enumerate(recommendations):

            label = (
                _RANK_LABELS[i]
                if i < len(_RANK_LABELS)
                else f"{i + 1}th best match"
            )

            facts.append(
                f"- {label}: {rec['product_name']} "
                f"(insurer: {rec['insurer_name']})"
            )
            facts.append(
                f"  Annual premium: exactly Rs "
                f"{rec['estimated_annual_premium_rs']} (do not round "
                f"or change this number)"
            )
            facts.append(f"  Why it fits: {rec['plain_language_pitch']}")
            facts.append(f"  Best suited for: {rec['best_for']}")

            all_matched_coverage.update(rec.get("matched_coverage", []))

        if common_coverage:
            facts.append(
                f"\n- IMPORTANT: ALL {len(recommendations)} options "
                f"above genuinely include: "
                f"{', '.join(sorted(common_coverage))}. Do not say "
                f"any of these are unavailable or not applicable -- "
                f"they apply to every option listed above."
            )

        comparisons = recommendations_result.get("comparisons", [])

        comparison_lines = [
            reason
            for comparison in comparisons
            for reason in comparison["reasons"]
        ]

        if comparison_lines:
            facts.append(
                "\nComparison notes between the options above -- each "
                "line already names both policies being compared; "
                "keep every number, name, and pairing exactly as "
                "written, do not mix numbers from different lines "
                "together:"
            )
            for line in comparison_lines:
                facts.append(f"- {line}")

        glossary_facts = (
            glossary.lookup_many(sorted(all_matched_coverage))
            if glossary is not None
            else []
        )

        prompt = (
            "You are writing a WhatsApp message to an Indian customer "
            "in Hinglish (mixed Hindi+English, casual WhatsApp style), "
            "warm and friendly.\n\n"
            "Present all the options below, ranked best to last, each "
            "with its price and why it fits. Then briefly mention the "
            "comparison notes so the customer understands the "
            "trade-offs between the options.\n\n"
            "Below are the ONLY facts you may use. Translate/localize "
            "the language into Hinglish, but do NOT change, round, "
            "recompute, or re-derive ANY number, Rs amount, or count "
            "in these facts -- copy every number exactly as written, "
            "and never combine or confuse numbers from two different "
            "comparison lines:\n\n"
            + "\n".join(facts)
        )

        prompt += _glossary_guardrail_text(glossary_facts)

        prompt += _regulatory_guardrail_text(_regulatory_requirement())

        return prompt

    def _format_comparison(context: ExecutionContext) -> str:

        comparison_result = context.get_variable("comparison_result", {})

        policy_a = comparison_result.get("policy_a", {})

        policy_b = comparison_result.get("policy_b", {})

        winner_id = comparison_result.get("winner_policy_id")

        winner_name = (
            policy_a.get("product_name")
            if winner_id == policy_a.get("policy_id")
            else policy_b.get("product_name")
        )

        facts = [
            f"- Policy A: {policy_a.get('product_name')}, annual "
            f"premium exactly Rs "
            f"{policy_a.get('estimated_annual_premium_rs')} (do not "
            f"round or change this number)",
            f"- Policy B: {policy_b.get('product_name')}, annual "
            f"premium exactly Rs "
            f"{policy_b.get('estimated_annual_premium_rs')} (do not "
            f"round or change this number)",
            f"- Better overall fit for this customer: {winner_name}",
        ]

        reasons = comparison_result.get("reasons", [])

        if reasons:
            facts.append(
                "- Reasons (each line is already complete -- keep "
                "every number and name exactly as written, do not mix "
                "numbers between lines):"
            )
            for reason in reasons:
                facts.append(f"  - {reason}")

        other_better_when = comparison_result.get("other_better_when")

        if other_better_when:
            facts.append(f"- Exception worth mentioning: {other_better_when}")

        all_matched_coverage = set(
            policy_a.get("matched_coverage", [])
        ) | set(policy_b.get("matched_coverage", []))

        glossary_facts = (
            glossary.lookup_many(sorted(all_matched_coverage))
            if glossary is not None
            else []
        )

        prompt = (
            "You are writing a WhatsApp message to an Indian customer "
            "in Hinglish (mixed Hindi+English, casual WhatsApp style), "
            "warm and friendly. The customer asked you to compare two "
            "specific policies by name.\n\n"
            "Below are the ONLY facts you may use. Translate/localize "
            "the language into Hinglish, but do NOT change, round, "
            "recompute, or re-derive ANY number, Rs amount, or count "
            "in these facts -- copy every number exactly as written, "
            "and never combine or confuse numbers from two different "
            "lines:\n\n"
            + "\n".join(facts)
        )

        prompt += _glossary_guardrail_text(glossary_facts)

        prompt += _regulatory_guardrail_text(_regulatory_requirement())

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
        elif prompt_kind == "format_comparison":
            prompt = _format_comparison(context)
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
    Build the shared Tool-node handler, dispatching on the node's
    configured tool_name (recommend_policies vs compare_policies).
    """

    def _recommend_parameters(context: ExecutionContext) -> dict[str, Any]:

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
        # not nullable, so an explicit None fails schema validation.
        budget_cap_rs = context.get_variable("budget_cap_rs")

        if budget_cap_rs is not None:
            parameters["budget_cap_rs"] = budget_cap_rs

        return parameters

    def _compare_parameters(context: ExecutionContext) -> dict[str, Any]:

        return {
            "policy_id_a": context.get_variable("policy_id_a"),
            "policy_id_b": context.get_variable("policy_id_b"),
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

    def tool_node_handler(
        node: WorkflowNode,
        context: ExecutionContext,
    ) -> dict[str, Any]:

        tool_name = node.configuration.get("tool_name")

        if tool_name == "recommend_policies":
            parameters = _recommend_parameters(context)
            output_key = "recommendations_result"
        elif tool_name == "compare_policies":
            parameters = _compare_parameters(context)
            output_key = "comparison_result"
        else:
            raise ValueError(
                f"Unknown tool_name '{tool_name}' for Tool node "
                f"'{node.id}'."
            )

        response = tool_service.execute(tool_name, parameters=parameters)

        if response.status == "failure":
            raise RuntimeError(f"{tool_name} tool failed: {response.error}")

        return {output_key: response.result}

    return tool_node_handler