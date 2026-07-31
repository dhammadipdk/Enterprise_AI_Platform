"""
Registers Policy Advisor's tools with a ToolService instance.
"""

from __future__ import annotations

from pathlib import Path

from enterprise_ai_platform.tool_engine import (
    PythonFunctionAdapter,
    ToolCategory,
    ToolDefinition,
    ToolService,
)

from enterprise_ai_platform.domains.insurance.policy_advisor.recommendation_engine import (
    PolicyRecommendationEngine,
)

_SHARED_PROPERTIES = {
    "vehicle_idv_rs": {"type": "number"},
    "vehicle_age_years": {"type": "integer"},
    "ncb_percent": {"type": "number"},
    "ev_flag": {"type": "boolean"},
    "coverage_priorities": {"type": "array", "items": {"type": "string"}},
    "budget_sensitivity_1to5": {"type": "integer"},
    "prefers_cashless": {"type": "boolean"},
    "annual_mileage_km": {"type": "number"},
    "financed_vehicle": {"type": "boolean"},
    "family_usage": {"type": "boolean"},
    "digital_affinity_1to5": {"type": "integer"},
    "protection_preference": {
        "type": "string",
        "enum": ["max_protection", "balanced", "budget_first"],
    },
    "wants_lowest_price": {"type": "boolean"},
    "flood_exposed": {"type": "boolean"},
    "risk_band": {"type": "string", "enum": ["low", "medium", "high"]},
    "theft_exposed": {"type": "boolean"},
    "age": {"type": "integer"},
    "commute_pattern": {
        "type": "string",
        "enum": [
            "daily_commute", "long_distance", "weekend_only", "family_errands",
        ],
    },
}

_RECOMMEND_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        **_SHARED_PROPERTIES,
        "budget_cap_rs": {"type": "number"},
        "top_n": {"type": "integer"},
    },
    "required": ["vehicle_idv_rs", "vehicle_age_years"],
}

_COMPARE_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "policy_id_a": {"type": "string"},
        "policy_id_b": {"type": "string"},
        **_SHARED_PROPERTIES,
    },
    "required": [
        "policy_id_a",
        "policy_id_b",
        "vehicle_idv_rs",
        "vehicle_age_years",
    ],
}


def register_policy_advisor_tools(
    tool_service: ToolService,
    catalog_path: Path | str,
    ontology_path: Path | str | None = None,
) -> None:
    """
    Register Policy Advisor's tools: recommend_policies (top-N ranked
    policies with cross-comparison) and compare_policies (two named
    policies, head-to-head).

    `ontology_path` (optional, additive) enables ontology-driven
    coverage bonuses; omitted, PolicyRecommendationEngine falls back
    to only its two explicit rules (financed_vehicle, family_usage).
    """

    engine = PolicyRecommendationEngine(catalog_path, ontology_path)

    tool_service.register_tool(
        ToolDefinition(
            name="recommend_policies",
            version="1.0.0",
            description=(
                "Deterministically rank eligible motor insurance "
                "policies for a customer profile, including ontology-"
                "driven coverage-relevance bonuses and cross-"
                "comparison notes between the top matches. The LLM "
                "must not re-rank or second-guess this tool's "
                "ordering -- it only formats this tool's result in "
                "natural language."
            ),
            category=ToolCategory.CUSTOM,
            input_schema=_RECOMMEND_INPUT_SCHEMA,
        ),
        PythonFunctionAdapter(engine.recommend_with_comparison),
    )

    tool_service.register_tool(
        ToolDefinition(
            name="compare_policies",
            version="1.0.0",
            description=(
                "Deterministically compare two named policies for a "
                "customer profile. The LLM must not re-decide the "
                "winner -- it only formats this tool's result in "
                "natural language."
            ),
            category=ToolCategory.CUSTOM,
            input_schema=_COMPARE_INPUT_SCHEMA,
        ),
        PythonFunctionAdapter(engine.compare),
    )