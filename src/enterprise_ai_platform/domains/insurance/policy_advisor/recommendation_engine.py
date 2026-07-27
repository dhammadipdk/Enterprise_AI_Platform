"""
Deterministic policy recommendation engine for the Policy Advisor
workflow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class PolicyRecommendationEngine:
    """
    Deterministic policy scoring and ranking against the real policy
    catalog (48 synthetic-but-structured motor products).

    Matches the architecture principle from the InsureAI deck: the
    LLM never ranks policies, it only formats already-ranked output
    in natural language. Every score here is a plain arithmetic
    function of visible catalog fields and the customer profile --
    nothing here is an LLM call, so it's fast, deterministic, and
    fully explainable.

    IMPORTANT: pandas reads CSV boolean columns back as numpy.bool_,
    not Python's native bool -- `numpy.True_ is True` evaluates to
    False. Every boolean flag check here uses truthiness (`if
    policy.get(flag):`), never identity (`is True`), specifically
    because of this. (Verified empirically before writing this file --
    an identity check here would have silently zeroed out every
    coverage-match score without raising any error.)

    This is a deliberately hand-designed scoring formula, not a
    reverse-engineered match of the source dataset's own premium/
    suitability numbers -- those appear to depend on additional
    factors not present in the visible columns (confirmed by testing
    several candidate formulas against real rows; none matched
    exactly). The dataset's existing recommendations are useful as a
    reference for explanation *style*, not as ground truth to
    replicate numerically.
    """

    _QUALITY_FIELDS = (
        "cashless_garage_score",
        "claim_support_score",
        "digital_servicing_score",
        "service_score",
    )

    def __init__(self, catalog_path: Path | str) -> None:

        self._catalog = pd.read_csv(catalog_path)

    def recommend(
        self,
        vehicle_idv_rs: float,
        vehicle_age_years: int,
        ncb_percent: float = 0,
        ev_flag: bool = False,
        coverage_priorities: list[str] | None = None,
        budget_sensitivity_1to5: int = 3,
        prefers_cashless: bool = False,
        budget_cap_rs: float | None = None,
        top_n: int = 3,
    ) -> dict[str, Any]:
        """
        Return the top `top_n` eligible policies ranked by
        suitability, plus a "why not the cheapest" explanation when
        the top pick isn't the lowest-premium eligible option.
        """

        coverage_priorities = coverage_priorities or []

        candidates: list[dict[str, Any]] = []

        for _, policy in self._catalog.iterrows():

            if not self._is_eligible(policy, vehicle_age_years, ev_flag):
                continue

            score, premium = self._score(
                policy,
                vehicle_idv_rs,
                ncb_percent,
                coverage_priorities,
                budget_sensitivity_1to5,
                prefers_cashless,
                budget_cap_rs,
            )

            matched_coverage = [
                c for c in coverage_priorities if policy.get(c)
            ]

            candidates.append(
                {
                    "policy_id": policy["policy_id"],
                    "product_name": policy["product_name"],
                    "insurer_name": policy["insurer_name_synthetic"],
                    "coverage_type": policy["coverage_type"],
                    "estimated_annual_premium_rs": premium,
                    "suitability_score": score,
                    "best_for": policy["best_for"],
                    "exclusion_tags": policy["exclusion_tags"],
                    "plain_language_pitch": policy["plain_language_pitch"],
                    "matched_coverage": matched_coverage,
                }
            )

        if not candidates:
            return {
                "recommendations": [],
                "total_eligible": 0,
                "why_not_cheapest": None,
                "message": (
                    "No eligible policies found for this vehicle profile "
                    "in the current catalog. This usually means the "
                    "vehicle's age exceeds every policy's maximum "
                    "insurable age -- flag for manual/specialist review "
                    "rather than silently returning nothing."
                ),
            }

        candidates.sort(key=lambda c: c["suitability_score"], reverse=True)

        top = candidates[:top_n]

        cheapest = min(
            candidates,
            key=lambda c: c["estimated_annual_premium_rs"],
        )

        why_not_cheapest = None

        if top[0]["policy_id"] != cheapest["policy_id"]:
            why_not_cheapest = (
                f"{cheapest['product_name']} is cheaper "
                f"(Rs {cheapest['estimated_annual_premium_rs']}) but "
                f"ranked lower: it matches "
                f"{len(cheapest['matched_coverage'])} of "
                f"{len(coverage_priorities)} priority coverages you "
                f"asked for, versus {len(top[0]['matched_coverage'])} "
                f"for the top recommendation."
            )

        return {
            "recommendations": top,
            "total_eligible": len(candidates),
            "why_not_cheapest": why_not_cheapest,
            "message": None,
        }

    @staticmethod
    def _is_eligible(
        policy: pd.Series,
        vehicle_age_years: int,
        ev_flag: bool,
    ) -> bool:

        max_age = policy.get("target_vehicle_age_max")

        if pd.notna(max_age) and vehicle_age_years > max_age:
            return False

        if policy.get("ev_only") and not ev_flag:
            return False

        return True

    @classmethod
    def _score(
        cls,
        policy: pd.Series,
        vehicle_idv: float,
        ncb_percent: float,
        coverage_priorities: list[str],
        budget_sensitivity_1to5: int,
        prefers_cashless: bool,
        budget_cap_rs: float | None,
    ) -> tuple[float, int]:

        premium = cls._estimate_premium(policy, vehicle_idv, ncb_percent)

        coverage_fit = (
            sum(1 for c in coverage_priorities if policy.get(c))
            / len(coverage_priorities)
            if coverage_priorities
            else 0.0
        )

        quality_denominator = 450.0 if prefers_cashless else 400.0

        cashless_weight = 1.5 if prefers_cashless else 1.0

        quality = (
            policy["cashless_garage_score"] * cashless_weight
            + policy["claim_support_score"]
            + policy["digital_servicing_score"]
            + policy["service_score"]
        ) / quality_denominator

        price_weight = budget_sensitivity_1to5 / 5.0

        over_budget_penalty = 0.0

        if budget_cap_rs is not None and premium > budget_cap_rs:
            over_budget_penalty = min(
                1.0,
                (premium - budget_cap_rs) / budget_cap_rs,
            )

        score = (
            coverage_fit * 45
            + quality * 35
            - price_weight * (premium / 1000) * 0.5
            - over_budget_penalty * 50
        )

        return round(score, 2), premium

    @staticmethod
    def _estimate_premium(
        policy: pd.Series,
        vehicle_idv: float,
        ncb_percent: float,
    ) -> int:

        base = vehicle_idv * policy["base_rate_pct"] + policy["fixed_fee_rs"]

        discounted = base * (1 - ncb_percent / 100)

        return round(discounted * policy["premium_multiplier"])
