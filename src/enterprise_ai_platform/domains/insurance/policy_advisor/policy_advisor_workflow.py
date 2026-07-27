"""
Policy Advisor workflow definition.
"""

from __future__ import annotations

from typing import Any

REQUIRED_SLOTS = ["vehicle_idv_rs", "vehicle_age_years"]

POLICY_ADVISOR_WORKFLOW: dict[str, Any] = {
    "name": "policy_advisor",
    "version": "1.0.0",
    "entry_node": "start",
    "nodes": [
        {"id": "start", "name": "Start", "node_type": "start"},
        {
            "id": "check_slots",
            "name": "Check Required Slots",
            "node_type": "decision",
            "outputs": ["has_required_info", "missing_required_info"],
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
            "outputs": ["recommendations_result"],
        },
        {
            "id": "format_explanation",
            "name": "Format Explanation",
            "node_type": "llm",
            "configuration": {"prompt_kind": "format_explanation"},
            "outputs": ["response_text"],
        },
        {"id": "end_ask", "name": "End (Asked Clarifying Question)", "node_type": "end"},
        {"id": "end_recommend", "name": "End (Recommended)", "node_type": "end"},
    ],
    "edges": [
        {"source": "start", "destination": "check_slots"},
        {
            "source": "check_slots",
            "destination": "get_recommendations",
            "condition": "has_required_info",
        },
        {
            "source": "check_slots",
            "destination": "ask_clarifying_question",
            "condition": "missing_required_info",
        },
        {"source": "ask_clarifying_question", "destination": "end_ask"},
        {"source": "get_recommendations", "destination": "format_explanation"},
        {"source": "format_explanation", "destination": "end_recommend"},
    ],
}
