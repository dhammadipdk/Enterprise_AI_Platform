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

from enterprise_ai_platform.domains.insurance.policy_advisor.explanation_composer import (
    ExplanationComposer,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.policy_advisor_workflow import (
    REQUIRED_SLOTS,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.risk_scoring_engine import (
    RiskScoringEngine,
)


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
    check ONE named variable's truthiness each. Naming both policies
    without also giving vehicle info still routes to the clarifying
    question, not straight to comparison.
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
    Build the shared LLM-node handler.

    For explanation/comparison, the LLM's job is deliberately narrow:
    retell ALREADY fact-checked, ALREADY correctly-attributed text
    (built by ExplanationComposer) in a warmer tone and in Hinglish --
    not to figure out which fact belongs where. See
    explanation_composer.py's docstring for why.
    """

    composer = ExplanationComposer()

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

    def _retelling_prompt(composed_text: str, intro: str) -> str:
        """
        The narrowed prompt: retell already-correct, already-attributed
        text. No facts to bind, no reasons to assign -- that work is
        already done by ExplanationComposer.
        """

        return (
            "You are an experienced, warm insurance agent talking to "
            "a customer on WhatsApp, in Hinglish (mixed Hindi+English, "
            f"casual conversational tone). {intro}\n\n"
            "Speak the way a real agent actually talks -- flowing "
            "sentences, no bullet points, no numbered lists, no bold "
            "headers, no labeled fields.\n\n"
            "Below is the exact information to retell -- it has "
            "already been fact-checked and correctly organized. "
            "Retell it faithfully in your own natural words. Do NOT "
            "change any number. Do NOT invent any additional fact, "
            "reason, or comparison beyond what is written here. Do "
            "NOT move any sentence to a different policy than the "
            "one it appears under below:\n\n"
            + composed_text
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
                f"You are a warm insurance agent. Retell this to the "
                f"customer in natural Hinglish (Hindi+English "
                f"WhatsApp style): {message}"
            )

        composed_text = composer.compose_recommendation_summary(
            recommendations_result
        )

        all_matched_coverage: set[str] = set()

        for rec in recommendations:
            all_matched_coverage.update(rec.get("matched_coverage", []))

        glossary_facts = (
            glossary.lookup_many(sorted(all_matched_coverage))
            if glossary is not None
            else []
        )

        prompt = _retelling_prompt(
            composed_text,
            intro=(
                "Present the options below, best match first, then "
                "how they compare -- like you're walking the customer "
                "through your recommendation."
            ),
        )

        prompt += _glossary_guardrail_text(glossary_facts)

        prompt += _regulatory_guardrail_text(_regulatory_requirement())

        return prompt

    def _format_comparison(context: ExecutionContext) -> str:

        comparison_result = context.get_variable("comparison_result", {})

        composed_text = composer.compose_comparison_summary(
            comparison_result
        )

        policy_a = comparison_result.get("policy_a", {})

        policy_b = comparison_result.get("policy_b", {})

        all_matched_coverage = set(
            policy_a.get("matched_coverage", [])
        ) | set(policy_b.get("matched_coverage", []))

        glossary_facts = (
            glossary.lookup_many(sorted(all_matched_coverage))
            if glossary is not None
            else []
        )

        prompt = _retelling_prompt(
            composed_text,
            intro=(
                "The customer asked you to compare two specific "
                "policies by name -- give them your honest "
                "professional take."
            ),
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

    Computes risk scoring inline here, right before building tool
    parameters -- matching the "risk_scoring_engine ->
    policy_catalog_lookup -> recommendation_ranker" pipeline shape the
    real agentic_tasks fixtures show, without needing a separate graph
    node for it.
    """

    risk_engine = RiskScoringEngine()

    def _compute_risk(context: ExecutionContext) -> dict[str, Any]:

        return risk_engine.score(
            residence_cluster=context.get_variable("residence_cluster"),
            city_risk_band=context.get_variable("city_risk_band"),
            flood_risk_band=context.get_variable("flood_risk_band"),
            commute_pattern=context.get_variable("commute_pattern"),
            annual_mileage_km=context.get_variable("annual_mileage_km"),
            theft_history=context.get_variable("theft_history", 0),
            previous_claims_3yr=context.get_variable("previous_claims_3yr", 0),
            at_fault_claims_3yr=context.get_variable("at_fault_claims_3yr", 0),
            traffic_violations_3yr=context.get_variable(
                "traffic_violations_3yr", 0
            ),
            anti_theft_device=context.get_variable(
                "anti_theft_device", False
            ),
            adas_level=context.get_variable("adas_level", 0),
            parking_type=context.get_variable("parking_type"),
            driving_experience_years=context.get_variable(
                "driving_experience_years"
            ),
            age=context.get_variable("age"),
        )

    def _shared_parameters(
        context: ExecutionContext,
        risk_result: dict[str, Any],
    ) -> dict[str, Any]:

        parameters = {
            "vehicle_idv_rs": context.get_variable("vehicle_idv_rs"),
            "vehicle_age_years": context.get_variable("vehicle_age_years"),
            "ncb_percent": context.get_variable("ncb_percent", 0),
            "ev_flag": context.get_variable("ev_flag", False),
            "coverage_priorities": context.get_variable(
                "coverage_priorities", []
            ),
            "budget_sensitivity_1to5": context.get_variable(
                "budget_sensitivity_1to5", 3
            ),
            "prefers_cashless": context.get_variable(
                "prefers_cashless", False
            ),
            "financed_vehicle": context.get_variable(
                "financed_vehicle", False
            ),
            "family_usage": context.get_variable("family_usage", False),
            "wants_lowest_price": context.get_variable(
                "wants_lowest_price", False
            ),
            # An explicitly-set flood_exposed/theft_exposed must never
            # be silently discarded just because we don't ALSO have
            # the raw factors to derive it independently -- an
            # explicit signal (e.g. from a future memory/extraction
            # layer that already inferred this from "I live in
            # Mumbai") is at least as trustworthy as a freshly-computed
            # one, so either being true is enough.
            "flood_exposed": (
                risk_result["flood_exposed"]
                or context.get_variable("flood_exposed", False)
            ),
            "risk_band": risk_result["risk_band"],
        }

        for optional_field in (
            "annual_mileage_km",
            "digital_affinity_1to5",
            "protection_preference",
        ):
            value = context.get_variable(optional_field)
            if value is not None:
                parameters[optional_field] = value

        return parameters

    def tool_node_handler(
        node: WorkflowNode,
        context: ExecutionContext,
    ) -> dict[str, Any]:

        tool_name = node.configuration.get("tool_name")

        if tool_name not in ("recommend_policies", "compare_policies"):
            raise ValueError(
                f"Unknown tool_name '{tool_name}' for Tool node "
                f"'{node.id}'."
            )

        risk_result = _compute_risk(context)

        parameters = _shared_parameters(context, risk_result)

        if tool_name == "compare_policies":
            parameters["policy_id_a"] = context.get_variable("policy_id_a")
            parameters["policy_id_b"] = context.get_variable("policy_id_b")
            output_key = "comparison_result"
        else:
            budget_cap_rs = context.get_variable("budget_cap_rs")
            if budget_cap_rs is not None:
                parameters["budget_cap_rs"] = budget_cap_rs
            output_key = "recommendations_result"

        response = tool_service.execute(tool_name, parameters=parameters)

        if response.status == "failure":
            raise RuntimeError(f"{tool_name} tool failed: {response.error}")

        return {output_key: response.result, "risk_assessment": risk_result}

    return tool_node_handler