"""
Policy Advisor workflow definition.
"""

from __future__ import annotations

from typing import Any

REQUIRED_SLOTS = ["vehicle_idv_rs", "vehicle_age_years"]

# Every field the extraction node can populate -- shared with the
# node's declared `outputs` so nothing extracted is silently dropped
# (WorkflowRuntime only promotes a node's DECLARED outputs into
# context variables; an undeclared key in a handler's return dict is
# simply not accessible downstream).
EXTRACTABLE_PROFILE_FIELDS = [
    "name",
    # Tier 1 -- hard required
    "vehicle_idv_rs",
    "vehicle_age_years",
    # Tier 2 -- inferred from message + world knowledge, never a
    # dedicated question
    "fuel_type",
    "ev_flag",
    "annual_mileage_km",
    "ncb_percent",
    "residence_cluster",
    "city_risk_band",
    "flood_risk_band",
    "commute_pattern",
    "financed_vehicle",
    "family_usage",
    "dependents",
    "vehicle_segment",
    "protection_preference",
    "wants_lowest_price",
    "coverage_priorities",
    "prefers_cashless",
    # Tier 3 -- only if volunteered, never asked, retained if learned
    "theft_history",
    "previous_claims_3yr",
    "at_fault_claims_3yr",
    "traffic_violations_3yr",
    "anti_theft_device",
    "adas_level",
    "parking_type",
    "driving_experience_years",
    "insurance_history_years",
    "digital_affinity_1to5",
    "telematics_opt_in",
    "prior_policy_lapse",
    "needs_plain_language_1to5",
    "age",
    # Metadata, not a profile fact
    "is_chitchat_only",
]

POLICY_ADVISOR_WORKFLOW: dict[str, Any] = {
    "name": "policy_advisor",
    "version": "4.0.0",
    "entry_node": "start",
    "nodes": [
        {"id": "start", "name": "Start", "node_type": "start"},
        {
            "id": "ensure_session",
            "name": "Ensure Session Identifier",
            "node_type": "task",
            "outputs": ["session_id"],
        },
        {
            "id": "extract_and_merge_profile",
            "name": "Extract And Merge Customer Profile",
            "node_type": "memory",
            "outputs": EXTRACTABLE_PROFILE_FIELDS,
        },
        {
            "id": "check_slots",
            "name": "Check Required Slots And Route",
            "node_type": "decision",
            "outputs": [
                "should_ask_clarifying",
                "should_compare",
                "should_recommend",
            ],
        },
        {
            "id": "ask_clarifying_question",
            "name": "Ask Clarifying Question",
            "node_type": "llm",
            "configuration": {"prompt_kind": "ask_clarifying_question"},
            "outputs": ["response_text"],
        },
        {
            "id": "get_recommendations",
            "name": "Get Policy Recommendations",
            "node_type": "tool",
            "configuration": {"tool_name": "recommend_policies"},
            "outputs": ["recommendations_result", "risk_assessment"],
        },
        {
            "id": "format_explanation",
            "name": "Format Explanation",
            "node_type": "llm",
            "configuration": {"prompt_kind": "format_explanation"},
            "outputs": ["response_text"],
        },
        {
            "id": "get_comparison",
            "name": "Get Policy Comparison",
            "node_type": "tool",
            "configuration": {"tool_name": "compare_policies"},
            "outputs": ["comparison_result", "risk_assessment"],
        },
        {
            "id": "format_comparison",
            "name": "Format Comparison Explanation",
            "node_type": "llm",
            "configuration": {"prompt_kind": "format_comparison"},
            "outputs": ["response_text"],
        },
        {"id": "end_ask", "name": "End (Asked Clarifying Question)", "node_type": "end"},
        {"id": "end_recommend", "name": "End (Recommended)", "node_type": "end"},
        {"id": "end_compare", "name": "End (Compared)", "node_type": "end"},
    ],
    "edges": [
        {"source": "start", "destination": "ensure_session"},
        {"source": "ensure_session", "destination": "extract_and_merge_profile"},
        {"source": "extract_and_merge_profile", "destination": "check_slots"},
        {
            "source": "check_slots",
            "destination": "ask_clarifying_question",
            "condition": "should_ask_clarifying",
        },
        {
            "source": "check_slots",
            "destination": "get_comparison",
            "condition": "should_compare",
        },
        {
            "source": "check_slots",
            "destination": "get_recommendations",
            "condition": "should_recommend",
        },
        {"source": "ask_clarifying_question", "destination": "end_ask"},
        {"source": "get_recommendations", "destination": "format_explanation"},
        {"source": "format_explanation", "destination": "end_recommend"},
        {"source": "get_comparison", "destination": "format_comparison"},
        {"source": "format_comparison", "destination": "end_compare"},
    ],
}