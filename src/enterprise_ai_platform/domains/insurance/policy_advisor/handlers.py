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
    EXTRACTABLE_PROFILE_FIELDS,
    REQUIRED_SLOTS,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.policy_name_resolver import (
    PolicyNameResolver,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.risk_scoring_engine import (
    RiskScoringEngine,
)
from enterprise_ai_platform.domains.insurance.policy_advisor.vehicle_info_resolver import (
    VehicleInfoResolver,
)

_SLOT_LABELS = {
    "vehicle_idv_rs": "vehicle's IDV (insured value) in rupees",
    "vehicle_age_years": "vehicle's age in years",
    "vehicle_segment": "vehicle type -- car, bike/two-wheeler, or commercial vehicle",
}


def check_required_slots_handler(
    node: WorkflowNode,
    context: ExecutionContext,
) -> dict[str, Any]:
    """
    Decision handler: FIRST checks whether this is a follow-up
    question about something already shown (highest priority -- if
    the customer is asking about their existing options, answering
    that takes precedence over collecting new info), THEN checks
    required-slot completeness and comparison-vs-recommendation
    routing, exactly as before.

    Produces four mutually exclusive flags -- WorkflowRuntime's edge
    conditions only check ONE named variable's truthiness each.
    """

    is_followup_question = context.get_variable("is_followup_question", False)

    has_last_shown = context.get_variable("_last_shown_summary") is not None

    if is_followup_question and has_last_shown:
        return {
            "should_answer_followup": True,
            "should_ask_clarifying": False,
            "should_compare": False,
            "should_recommend": False,
        }

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
        "should_answer_followup": False,
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
    """

    composer = ExplanationComposer(glossary)

    _SLOT_LABELS_LOCAL = _SLOT_LABELS

    def _ask_clarifying_question(context: ExecutionContext) -> str:

        missing_slots = context.get_metadata("missing_slots", [])

        readable_missing = [
            _SLOT_LABELS_LOCAL.get(slot, slot) for slot in missing_slots
        ]

        is_chitchat_only = context.get_variable("is_chitchat_only", False)

        chitchat_note = (
            "The customer's message was just a greeting/small talk "
            "with no insurance content -- warmly acknowledge it "
            "first, in a natural way, before asking for what's "
            "missing. "
            if is_chitchat_only
            else ""
        )

        return (
            f"{chitchat_note}Customer wants motor insurance advice "
            f"on WhatsApp. We still need: {', '.join(readable_missing)}. "
            f"Ask ONE short, friendly question in Hinglish "
            f"(Hindi+English WhatsApp style) to get this missing "
            f"information. Do not ask for anything else, and do not "
            f"repeat information already known."
        )

    def _answer_followup(context: ExecutionContext) -> str:

        customer_message = context.get_variable("customer_message", "")

        last_shown_summary = context.get_variable("_last_shown_summary", "")

        return (
            "You are an experienced, warm insurance agent talking to "
            "a customer on WhatsApp, in Hinglish (mixed Hindi+English, "
            "casual conversational tone). The customer previously "
            "received this information from you:\n\n"
            f"{last_shown_summary}\n\n"
            f'The customer is now asking a follow-up question: '
            f'"{customer_message}"\n\n'
            "Answer their question using ONLY the facts above -- do "
            "NOT invent any new fact, number, or comparison not "
            "already stated above. If their question asks about "
            "something not covered by these facts, say so honestly "
            "and offer to help them get that specific information "
            "rather than guessing. No bullet points, numbered lists, "
            "or bold headers -- warm, natural, flowing sentences."
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
            f"discontinuance terms, refund policy, risks) if they "
            f"were explicitly given to you in the facts above. This "
            f"applies even if you phrase it as a possibility or hedge "
            f"it with words like 'might' or 'may' -- a hedged "
            f"invented claim is still an invented claim. If this "
            f"requirement mentions something you have no specific "
            f"facts about, say ONLY that details are available on "
            f"request -- do not describe, speculate about, or hint "
            f"at what those details might be, even vaguely.\n"
            f"This must be woven into the SAME flowing Hinglish "
            f"paragraphs as the rest of your message -- do NOT add "
            f"separate labeled sections like 'Details:', 'Risks:', "
            f"or 'Discontinuance:', and do NOT switch to plain "
            f"English for this part. One continuous reply, same "
            f"style throughout, not a form."
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

        return (
            "You are an experienced, warm insurance agent talking to "
            "a customer on WhatsApp, in Hinglish (mixed Hindi+English, "
            f"casual conversational tone). {intro}\n\n"
            "Everything below is ALREADY DECIDED and ALREADY "
            "CORRECTLY WORDED, including every comparison (which "
            "policy costs more, which scores higher on what). Your "
            "job is to TRANSLATE this into natural Hinglish, sentence "
            "by sentence -- NOT to creatively rephrase, restructure, "
            "recompute, or reconsider any conclusion. If a sentence "
            "says one policy is MORE expensive or scores LOWER, your "
            "Hinglish translation must say the exact same thing, just "
            "in Hinglish words. Do not use bullet points, numbered "
            "lists, or bold headers -- flowing spoken sentences, but "
            "a faithful translation of the meaning below, not a "
            "creative rewrite:\n\n"
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
        elif prompt_kind == "answer_followup":
            prompt = _answer_followup(context)
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


def ensure_session_handler(
    node: WorkflowNode,
    context: ExecutionContext,
) -> dict[str, Any]:
    """
    First node in the graph: preserves an existing session_id if the
    caller supplied one, or generates a new one if not.
    """

    session_id = context.get_variable("session_id")

    if session_id is None:
        import uuid

        session_id = str(uuid.uuid4())

    return {"session_id": session_id}


def make_tool_node_handler(
    tool_service: ToolService,
    catalog_path: Any,
    memory_service: Any | None = None,
) -> Callable[[WorkflowNode, ExecutionContext], dict[str, Any]]:
    """
    Build the shared Tool-node handler, dispatching on the node's
    configured tool_name (recommend_policies vs compare_policies).

    Also persists a snapshot of what was just shown to the customer
    (a composed summary + the shown policy_ids) back into the SAME
    session profile memory -- this is what enables both natural-
    language "compare X vs Y" resolution (matching against what the
    customer was actually just shown, not the whole catalog) and
    follow-up question answering (answering from the exact facts
    already given, without re-running recommend/compare and risking
    a different result).
    """

    risk_engine = RiskScoringEngine()
    vehicle_info_resolver = VehicleInfoResolver()
    composer = ExplanationComposer()

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
            "flood_exposed": (
                risk_result["flood_exposed"]
                or context.get_variable("flood_exposed", False)
            ),
            "theft_exposed": (
                risk_result["theft_exposed"]
                or context.get_variable("theft_exposed", False)
            ),
            "risk_band": risk_result["risk_band"],
        }

        resolved_vehicle_info = vehicle_info_resolver.resolve(
            vehicle_segment=context.get_variable("vehicle_segment"),
            vehicle_registration_number=context.get_variable(
                "vehicle_registration_number"
            ),
        )

        parameters["vehicle_category"] = resolved_vehicle_info["vehicle_category"]

        for optional_field in (
            "annual_mileage_km",
            "digital_affinity_1to5",
            "protection_preference",
            "age",
            "commute_pattern",
        ):
            value = context.get_variable(optional_field)
            if value is not None:
                parameters[optional_field] = value

        return parameters

    def _persist_last_shown(
        context: ExecutionContext,
        shown_policy_ids: list[str],
        composed_summary: str,
    ) -> None:

        if memory_service is None:
            return

        session_id = context.get_variable("session_id")

        current_profile = {
            field: context.get_variable(field)
            for field in EXTRACTABLE_PROFILE_FIELDS
            if context.get_variable(field) is not None
        }

        current_profile["_last_shown_policy_ids"] = shown_policy_ids

        current_profile["_last_shown_summary"] = composed_summary

        try:
            from enterprise_ai_platform.memory_engine import MemoryType

            memory_service.store(
                memory_type=MemoryType.SEMANTIC,
                content=current_profile,
                collection=f"policy_advisor_profile:{session_id}",
            )
        except Exception:
            pass

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

        result = response.result

        if tool_name == "recommend_policies":
            shown_ids = [r["policy_id"] for r in result.get("recommendations", [])]
            composed_summary = composer.compose_recommendation_summary(result)
        else:
            shown_ids = [
                result.get("policy_a", {}).get("policy_id"),
                result.get("policy_b", {}).get("policy_id"),
            ]
            composed_summary = composer.compose_comparison_summary(result)

        _persist_last_shown(context, shown_ids, composed_summary)

        return {
            output_key: result,
            "risk_assessment": risk_result,
            "vehicle_category": parameters["vehicle_category"],
        }

    return tool_node_handler


_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": ["string", "null"]},
        "vehicle_idv_rs": {"type": ["number", "null"]},
        "vehicle_age_years": {"type": ["integer", "null"]},
        "fuel_type": {"type": ["string", "null"]},
        "ev_flag": {"type": ["boolean", "null"]},
        "annual_mileage_km": {"type": ["number", "null"]},
        "ncb_percent": {"type": ["number", "null"]},
        "residence_cluster": {
            "type": ["string", "null"],
            "enum": [
                None, "coastal_flood_prone", "metro_high_theft",
                "urban_dense", "hilly_low_density", "suburban", "rural",
            ],
        },
        "vehicle_registration_number": {"type": ["string", "null"]},
        "city_risk_band": {"type": ["string", "null"], "enum": [None, "low", "medium", "high"]},
        "flood_risk_band": {"type": ["string", "null"], "enum": [None, "low", "medium", "high"]},
        "commute_pattern": {
            "type": ["string", "null"],
            "enum": [None, "daily_commute", "long_distance", "weekend_only", "family_errands"],
        },
        "financed_vehicle": {"type": ["boolean", "null"]},
        "family_usage": {"type": ["boolean", "null"]},
        "dependents": {"type": ["integer", "null"]},
        "vehicle_segment": {"type": ["string", "null"]},
        "protection_preference": {
            "type": ["string", "null"],
            "enum": [None, "max_protection", "balanced", "budget_first"],
        },
        "wants_lowest_price": {"type": ["boolean", "null"]},
        "coverage_priorities": {"type": ["array", "null"], "items": {"type": "string"}},
        "prefers_cashless": {"type": ["boolean", "null"]},
        "theft_history": {"type": ["integer", "null"]},
        "previous_claims_3yr": {"type": ["integer", "null"]},
        "at_fault_claims_3yr": {"type": ["integer", "null"]},
        "traffic_violations_3yr": {"type": ["integer", "null"]},
        "anti_theft_device": {"type": ["boolean", "null"]},
        "adas_level": {"type": ["integer", "null"]},
        "parking_type": {
            "type": ["string", "null"],
            "enum": [None, "covered_society", "gated", "street", "open_lot"],
        },
        "driving_experience_years": {"type": ["number", "null"]},
        "insurance_history_years": {"type": ["number", "null"]},
        "digital_affinity_1to5": {"type": ["integer", "null"]},
        "telematics_opt_in": {"type": ["boolean", "null"]},
        "prior_policy_lapse": {"type": ["boolean", "null"]},
        "needs_plain_language_1to5": {"type": ["integer", "null"]},
        "age": {"type": ["integer", "null"]},
        "is_chitchat_only": {"type": "boolean"},
        "is_followup_question": {"type": "boolean"},
        "comparison_policy_name_a": {"type": ["string", "null"]},
        "comparison_policy_name_b": {"type": ["string", "null"]},
    },
    "required": [],
}

_RISK_LEVEL_NORMALIZE = {
    "low": "low", "medium": "medium", "high": "high",
    "very_high": "high", "extreme": "high",
}


def make_extraction_handler(
    model_service: ModelService,
    memory_service: Any | None = None,
    location_risk: Any | None = None,
    policy_name_resolver: Any | None = None,
    model_name: str = "explanation_model",
) -> Callable[[WorkflowNode, ExecutionContext], dict[str, Any]]:
    """
    Build the profile extraction/merge handler (NodeType.MEMORY).

    `policy_name_resolver` (a PolicyNameResolver) resolves
    comparison_policy_name_a/b (extracted by the LLM as free text,
    e.g. "ClaimEase ThirdParty") into real policy_id_a/policy_id_b,
    preferring a match against `_last_shown_policy_ids` (what the
    customer was actually just shown) before falling back to the
    whole catalog.
    """

    def extraction_handler(
        node: WorkflowNode,
        context: ExecutionContext,
    ) -> dict[str, Any]:

        session_id = context.get_variable("session_id")

        existing_profile: dict[str, Any] = {}

        if memory_service is not None:

            try:
                from enterprise_ai_platform.memory_engine import (
                    MemoryQuery,
                    MemoryType,
                )

                results = memory_service.search(
                    MemoryQuery(
                        collection=f"policy_advisor_profile:{session_id}",
                        memory_type=MemoryType.SEMANTIC,
                        limit=1,
                    )
                )

                if results:
                    existing_profile = dict(results[0].item.content)

            except Exception:
                existing_profile = {}

        last_asked_about = existing_profile.pop("_last_asked_about", [])

        customer_message = context.get_variable("customer_message")

        if customer_message is None:
            existing_profile["is_chitchat_only"] = False
            existing_profile["is_followup_question"] = False
            return existing_profile

        known_facts_text = (
            "\n".join(
                f"- {key}: {value}"
                for key, value in existing_profile.items()
                if value is not None and not key.startswith("_")
            )
            or "None yet."
        )

        last_asked_text = (
            f"\n\nIMPORTANT: you just asked the customer for: "
            f"{', '.join(last_asked_about)}. If their new message is "
            f"short, a bare number, or otherwise ambiguous on its own, "
            f"it is very likely a direct answer to that specific "
            f"question -- interpret it in that light rather than "
            f"leaving it null."
            if last_asked_about
            else ""
        )

        has_last_shown = existing_profile.get("_last_shown_summary") is not None

        followup_hint = (
            "\n\nThe customer was already shown some policy "
            "recommendation(s) or comparison earlier in this "
            "conversation. Set is_followup_question to true if their "
            "new message is asking about, clarifying, or requesting "
            "more explanation of what they were already shown (e.g. "
            "'explain the difference', 'why is this one better', "
            "'what does that mean'), rather than giving new "
            "information or making a new request. If they name two "
            "specific policies to compare, extract those names into "
            "comparison_policy_name_a/comparison_policy_name_b "
            "exactly as the customer phrased them."
            if has_last_shown
            else ""
        )

        prompt = (
            "Extract insurance-relevant facts from the customer's "
            "message below. Only fill in a field if the message "
            "actually supports it -- leave anything not mentioned as "
            "null. Do not guess at fields with no basis in the "
            "message. Set is_chitchat_only to true only if the "
            "ENTIRE message is just a greeting or small talk with no "
            "insurance-relevant content at all, AND does not answer "
            "a question we just asked."
            f"{last_asked_text}"
            f"{followup_hint}\n\n"
            f"Facts already known from earlier in this conversation "
            f"(do not contradict these unless the new message clearly "
            f"updates them):\n{known_facts_text}\n\n"
            f'Customer\'s new message: "{customer_message}"'
        )

        try:
            response = model_service.execute(
                model_name,
                prompt,
                response_schema=_EXTRACTION_SCHEMA,
            )
            extracted = response.structured_output or {}
            context.set_metadata("extraction_error", None)
        except Exception as error:
            extracted = {}
            context.set_metadata("extraction_error", str(error))

        if location_risk is not None:

            city_match = location_risk.match_city(customer_message)

            if city_match is not None:

                normalized_flood = _RISK_LEVEL_NORMALIZE.get(
                    city_match["flood_risk"], city_match["flood_risk"]
                )
                normalized_theft = _RISK_LEVEL_NORMALIZE.get(
                    city_match["theft_risk"], city_match["theft_risk"]
                )

                extracted["flood_risk_band"] = normalized_flood
                extracted["city_risk_band"] = normalized_theft

                if normalized_flood == "high":
                    extracted["residence_cluster"] = "coastal_flood_prone"
                elif normalized_theft == "high":
                    extracted["residence_cluster"] = "metro_high_theft"

        # Resolve named policy comparison mentions to real policy_ids,
        # preferring what was just shown to this customer.
        if policy_name_resolver is not None:

            name_a = extracted.get("comparison_policy_name_a")
            name_b = extracted.get("comparison_policy_name_b")

            if name_a and name_b:

                last_shown_ids = existing_profile.get("_last_shown_policy_ids", [])

                resolved_a = policy_name_resolver.resolve(name_a, last_shown_ids)
                resolved_b = policy_name_resolver.resolve(name_b, last_shown_ids)

                if resolved_a is not None and resolved_b is not None:
                    extracted["policy_id_a"] = resolved_a
                    extracted["policy_id_b"] = resolved_b

        merged_profile = dict(existing_profile)

        for key, value in extracted.items():
            if key in (
                "is_chitchat_only",
                "is_followup_question",
                "comparison_policy_name_a",
                "comparison_policy_name_b",
            ):
                continue
            if value is not None:
                merged_profile[key] = value

        still_missing = [
            slot for slot in REQUIRED_SLOTS if merged_profile.get(slot) is None
        ]

        profile_to_store = dict(merged_profile)
        profile_to_store["_last_asked_about"] = still_missing

        if memory_service is not None:

            try:
                from enterprise_ai_platform.memory_engine import MemoryType

                memory_service.store(
                    memory_type=MemoryType.SEMANTIC,
                    content=profile_to_store,
                    collection=f"policy_advisor_profile:{session_id}",
                )
            except Exception:
                pass

        context.set_metadata("extracted_name_for_redaction", extracted.get("name"))

        merged_profile["is_chitchat_only"] = extracted.get("is_chitchat_only", False)
        merged_profile["is_followup_question"] = extracted.get(
            "is_followup_question", False
        )

        # policy_id_a/policy_id_b resolved above aren't part of the
        # DECLARED profile fields (they're routing signals, not
        # persisted customer facts) -- set directly for THIS turn's
        # context promotion. They are NOT added to
        # EXTRACTABLE_PROFILE_FIELDS's persisted set, so a resolved
        # comparison request doesn't leak into a later, unrelated turn.
        if "policy_id_a" in extracted:
            merged_profile["policy_id_a"] = extracted["policy_id_a"]
            merged_profile["policy_id_b"] = extracted["policy_id_b"]

        return merged_profile

    return extraction_handler