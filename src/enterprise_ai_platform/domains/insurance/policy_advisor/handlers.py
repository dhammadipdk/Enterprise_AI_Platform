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
from enterprise_ai_platform.domains.insurance.policy_advisor.risk_scoring_engine import (
    RiskScoringEngine,
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
        for any reason.
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

    def _facts_to_natural_prompt(
        facts: list[str],
        situational_reasons: list[str],
        intro: str,
    ) -> str:
        """
        Shared prompt-building for both explanation and comparison --
        explicitly instructs against mirroring the fact list's own
        structure in the output (labels, bullets, headers), which is
        what caused an earlier "form-filled" style response. The fact
        list itself stays structured internally (for the model to
        read precisely) -- only the OUTPUT is asked to be natural
        prose.
        """

        prompt = (
            "You are an experienced, warm human insurance agent "
            "replying to a customer on WhatsApp, in Hinglish "
            "(mixed Hindi+English, casual conversational tone). "
            f"{intro}\n\n"
            "Speak the way a real agent actually talks -- flowing "
            "sentences, like you're chatting with someone in person. "
            "Do NOT use bullet points, numbered lists, bold headers, "
            "or labeled fields (no 'Price:', no 'Best for:', no "
            "'Policy name:'). Weave the facts into natural "
            "paragraphs instead.\n\n"
            "Below are the ONLY facts you may use. You may rephrase "
            "and reorder freely, but do NOT change, round, recompute, "
            "or re-derive ANY number, Rs amount, or count -- copy "
            "every number exactly as it appears, and never combine "
            "or confuse numbers from two different facts:\n\n"
            + "\n".join(facts)
        )

        if situational_reasons:
            prompt += (
                "\n\nThese specific reasons matter for THIS customer "
                "-- mention them naturally as part of your "
                "explanation (e.g. 'roadside assistance is useful "
                "here since you drive long distance often'), don't "
                "just list them:\n"
                + "\n".join(f"- {r}" for r in situational_reasons)
            )

        return prompt

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
                f"Explain this to the customer warmly, as a real "
                f"insurance agent would, in Hinglish (Hindi+English "
                f"WhatsApp style): {message}"
            )

        facts: list[str] = []

        all_matched_coverage: set[str] = set()

        common_coverage = set(recommendations[0].get("matched_coverage", []))

        for rec in recommendations[1:]:
            common_coverage &= set(rec.get("matched_coverage", []))

        situational_reasons: list[str] = []

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

            situational_reasons.extend(rec.get("match_reasons", []))

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

        prompt = _facts_to_natural_prompt(
            facts,
            situational_reasons,
            intro=(
                "Present the options below, best match first, "
                "explaining what each is and why it fits, then "
                "mention how they compare -- like you're walking the "
                "customer through your recommendation."
            ),
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

        situational_reasons = (
            policy_a.get("match_reasons", [])
            + policy_b.get("match_reasons", [])
        )

        all_matched_coverage = set(
            policy_a.get("matched_coverage", [])
        ) | set(policy_b.get("matched_coverage", []))

        glossary_facts = (
            glossary.lookup_many(sorted(all_matched_coverage))
            if glossary is not None
            else []
        )

        prompt = _facts_to_natural_prompt(
            facts,
            situational_reasons,
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
            "flood_exposed": risk_result["flood_exposed"],
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