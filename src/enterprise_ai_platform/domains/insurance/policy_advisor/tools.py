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

_RECOMMEND_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "vehicle_idv_rs": {"type": "number"},
        "vehicle_age_years": {"type": "integer"},
        "ncb_percent": {"type": "number"},
        "ev_flag": {"type": "boolean"},
        "coverage_priorities": {
            "type": "array",
            "items": {"type": "string"},
        },
        "budget_sensitivity_1to5": {"type": "integer"},
        "prefers_cashless": {"type": "boolean"},
        "budget_cap_rs": {"type": "number"},
        "top_n": {"type": "integer"},
    },
    "required": ["vehicle_idv_rs", "vehicle_age_years"],
}


def register_policy_advisor_tools(
    tool_service: ToolService,
    catalog_path: Path | str,
) -> None:
    """
    Register the deterministic policy recommendation tool.
    """

    engine = PolicyRecommendationEngine(catalog_path)

    tool_service.register_tool(
        ToolDefinition(
            name="recommend_policies",
            version="1.0.0",
            description=(
                "Deterministically rank eligible motor insurance "
                "policies for a customer profile. The LLM must not "
                "re-rank or second-guess this tool's ordering -- it "
                "only formats the result in natural language."
            ),
            category=ToolCategory.CUSTOM,
            input_schema=_RECOMMEND_INPUT_SCHEMA,
        ),
        PythonFunctionAdapter(engine.recommend),
    )
