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
    Deterministic policy scoring, ranking, and comparison against the
    real policy catalog (48 synthetic-but-structured motor products).

    Matches the architecture principle from the InsureAI deck: the
    LLM never ranks or compares policies, it only formats already-
    computed output in natural language. Every score here is a plain
    arithmetic function of visible catalog fields and the customer
    profile -- nothing here is an LLM call, so it's fast,
    deterministic, and fully explainable.

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
                "comparisons": [],
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

    def recommend_with_comparison(
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
        Same as recommend(), but additionally computes pairwise
        comparison reasons between every pair of the returned top_n
        policies -- reusing the same premium/coverage-match reasoning
        compare() uses, just applied within one ranked set instead of
        two arbitrarily-named policies.

        This is what the Policy Advisor workflow's recommend_policies
        tool actually calls -- customers see all top_n options
        side-by-side with their trade-offs, not just the single best
        match.
        """

        result = self.recommend(
            vehicle_idv_rs=vehicle_idv_rs,
            vehicle_age_years=vehicle_age_years,
            ncb_percent=ncb_percent,
            ev_flag=ev_flag,
            coverage_priorities=coverage_priorities,
            budget_sensitivity_1to5=budget_sensitivity_1to5,
            prefers_cashless=prefers_cashless,
            budget_cap_rs=budget_cap_rs,
            top_n=top_n,
        )

        recommendations = result["recommendations"]

        comparisons = []

        for i in range(len(recommendations)):
            for j in range(i + 1, len(recommendations)):

                reasons = self._pairwise_reasons(
                    recommendations[i],
                    recommendations[j],
                    coverage_priorities or [],
                )

                comparisons.append(
                    {
                        "policy_a_id": recommendations[i]["policy_id"],
                        "policy_b_id": recommendations[j]["policy_id"],
                        "reasons": reasons,
                    }
                )

        result["comparisons"] = comparisons

        return result

    def compare(
        self,
        policy_id_a: str,
        policy_id_b: str,
        vehicle_idv_rs: float,
        vehicle_age_years: int,
        ncb_percent: float = 0,
        ev_flag: bool = False,
        coverage_priorities: list[str] | None = None,
        budget_sensitivity_1to5: int = 3,
        prefers_cashless: bool = False,
    ) -> dict[str, Any]:
        """
        Compare two named policies for one customer profile,
        deterministically -- reuses the same scoring/premium logic
        recommend() uses, applied to two specific policies instead of
        ranking the whole catalog.

        Raises KeyError if either policy_id is unknown.
        """

        coverage_priorities = coverage_priorities or []

        policy_a = self._get_policy_row(policy_id_a)
        policy_b = self._get_policy_row(policy_id_b)

        score_a, premium_a = self._score(
            policy_a,
            vehicle_idv_rs,
            ncb_percent,
            coverage_priorities,
            budget_sensitivity_1to5,
            prefers_cashless,
            None,
        )

        score_b, premium_b = self._score(
            policy_b,
            vehicle_idv_rs,
            ncb_percent,
            coverage_priorities,
            budget_sensitivity_1to5,
            prefers_cashless,
            None,
        )

        matched_a = [c for c in coverage_priorities if policy_a.get(c)]

        matched_b = [c for c in coverage_priorities if policy_b.get(c)]

        winner_is_a = score_a >= score_b

        winner_id = policy_id_a if winner_is_a else policy_id_b

        reasons: list[str] = []

        if premium_a != premium_b:
            cheaper = "A" if premium_a < premium_b else "B"
            diff = abs(premium_a - premium_b)
            reasons.append(f"Policy {cheaper} is Rs {diff} cheaper per year")

        if len(matched_a) != len(matched_b):
            reasons.append(
                f"Policy A matches {len(matched_a)}/"
                f"{len(coverage_priorities)} priority coverages vs "
                f"Policy B's {len(matched_b)}/{len(coverage_priorities)}"
            )

        if (
            policy_a["cashless_garage_score"]
            != policy_b["cashless_garage_score"]
        ):
            reasons.append(
                f"Cashless garage score: A="
                f"{policy_a['cashless_garage_score']} vs B="
                f"{policy_b['cashless_garage_score']}"
            )

        other_better_when = None

        if premium_a != premium_b:

            cheaper_id = (
                policy_id_a if premium_a < premium_b else policy_id_b
            )

            if cheaper_id != winner_id:

                cheaper_name = (
                    policy_a["product_name"]
                    if cheaper_id == policy_id_a
                    else policy_b["product_name"]
                )

                other_better_when = (
                    f"{cheaper_name} may still suit a customer who "
                    f"prioritizes lowest price over coverage breadth."
                )

        return {
            "policy_a": {
                "policy_id": policy_id_a,
                "product_name": policy_a["product_name"],
                "suitability_score": score_a,
                "estimated_annual_premium_rs": premium_a,
                "matched_coverage": matched_a,
            },
            "policy_b": {
                "policy_id": policy_id_b,
                "product_name": policy_b["product_name"],
                "suitability_score": score_b,
                "estimated_annual_premium_rs": premium_b,
                "matched_coverage": matched_b,
            },
            "winner_policy_id": winner_id,
            "reasons": reasons,
            "other_better_when": other_better_when,
        }

    @staticmethod
    def _pairwise_reasons(
        rec_a: dict[str, Any],
        rec_b: dict[str, Any],
        coverage_priorities: list[str],
    ) -> list[str]:

        reasons: list[str] = []

        premium_a = rec_a["estimated_annual_premium_rs"]

        premium_b = rec_b["estimated_annual_premium_rs"]

        if premium_a != premium_b:
            cheaper = (
                rec_a["product_name"]
                if premium_a < premium_b
                else rec_b["product_name"]
            )
            diff = abs(premium_a - premium_b)
            reasons.append(f"{cheaper} is Rs {diff} cheaper per year")

        matched_a = len(rec_a["matched_coverage"])

        matched_b = len(rec_b["matched_coverage"])

        if matched_a != matched_b and coverage_priorities:
            reasons.append(
                f"{rec_a['product_name']} matches {matched_a}/"
                f"{len(coverage_priorities)} priority coverages vs "
                f"{rec_b['product_name']}'s {matched_b}/"
                f"{len(coverage_priorities)}"
            )

        return reasons

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

    def _get_policy_row(self, policy_id: str) -> pd.Series:

        matches = self._catalog[self._catalog["policy_id"] == policy_id]

        if matches.empty:
            raise KeyError(f"No policy found with policy_id '{policy_id}'.")

        return matches.iloc[0]

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