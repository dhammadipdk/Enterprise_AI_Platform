"""
Deterministic policy recommendation engine for the Policy Advisor
workflow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

# Real customer_profiles.coverage_priorities values include terms that
# are NOT policy_catalog boolean column names -- they're preference
# signals about HOW to weight scoring dimensions, not coverage flags
# to match against.
_PREFERENCE_TERMS = {"digital_servicing", "cashless_strength", "price_control"}

_RISK_LOADING = {"high": 1.15, "medium": 1.0, "low": 0.95}

# Used for genuine, honest tradeoff explanations between any two
# scored policies -- e.g. explaining why a pricier option outranks a
# cheaper one on quality grounds, not just "it costs more." Threshold
# exists so noise-level score differences (e.g. 89 vs 91) don't get
# reported as if they were meaningful.
_QUALITY_FIELDS = [
    ("cashless_garage_score", "cashless garage network"),
    ("claim_support_score", "claim support"),
    ("digital_servicing_score", "digital servicing"),
    ("service_score", "overall service"),
]

_QUALITY_DIFF_THRESHOLD = 5


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

    Every comparison this engine produces (top-vs-cheapest,
    pairwise-among-top-N) goes through the SAME _compare_two_policies
    method, which reports not just price differences but the
    strongest quality-score differentiators driving a ranking --
    added specifically because ranking a pricier policy #1 without
    ever surfacing WHY (e.g. its actually-stronger claim support or
    cashless network) left the customer with no real justification
    for the recommendation, just a price tag. When nothing genuinely
    differs beyond price, the comparison says so honestly rather than
    manufacturing a reason.

    IMPORTANT: pandas reads CSV boolean columns back as numpy.bool_,
    not Python's native bool -- `numpy.True_ is True` evaluates to
    False. Every boolean flag check here uses truthiness, never
    identity.

    This is a deliberately hand-designed scoring formula, not a
    reverse-engineered match of the source dataset's own premium/
    suitability numbers -- confirmed by testing several candidate
    formulas against real rows; none matched exactly.
    """

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
        annual_mileage_km: float | None = None,
        financed_vehicle: bool = False,
        family_usage: bool = False,
        digital_affinity_1to5: int | None = None,
        protection_preference: str | None = None,
        wants_lowest_price: bool = False,
        flood_exposed: bool = False,
        risk_band: str | None = None,
    ) -> dict[str, Any]:
        """
        Return the top `top_n` eligible policies ranked by
        suitability, plus a genuine, honest explanation of why the
        top pick was chosen over the cheapest eligible option when
        they differ.
        """

        flag_terms, preference_terms = self._parse_coverage_priorities(
            coverage_priorities
        )

        candidates: list[dict[str, Any]] = []

        for _, policy in self._catalog.iterrows():

            if not self._is_eligible(
                policy, vehicle_age_years, ev_flag, annual_mileage_km
            ):
                continue

            score, premium, match_reasons = self._score(
                policy,
                vehicle_idv_rs,
                ncb_percent,
                flag_terms,
                preference_terms,
                budget_sensitivity_1to5,
                prefers_cashless,
                budget_cap_rs,
                annual_mileage_km,
                financed_vehicle,
                family_usage,
                digital_affinity_1to5,
                protection_preference,
                wants_lowest_price,
                flood_exposed,
                risk_band,
            )

            matched_coverage = [c for c in flag_terms if policy.get(c)]

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
                    "match_reasons": match_reasons,
                    "cashless_garage_score": policy["cashless_garage_score"],
                    "claim_support_score": policy["claim_support_score"],
                    "digital_servicing_score": policy[
                        "digital_servicing_score"
                    ],
                    "service_score": policy["service_score"],
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
                    "vehicle's age or mileage exceeds every policy's "
                    "limits -- flag for manual/specialist review rather "
                    "than silently returning nothing."
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

            comparison_reasons = self._compare_two_policies(
                top[0], cheapest, flag_terms
            )

            if comparison_reasons:
                why_not_cheapest = (
                    f"{top[0]['product_name']} was chosen as the top "
                    f"pick over the cheaper {cheapest['product_name']} "
                    f"because: {'; '.join(comparison_reasons)}."
                )
            else:
                why_not_cheapest = (
                    f"{cheapest['product_name']} (Rs "
                    f"{cheapest['estimated_annual_premium_rs']}) offers "
                    f"very similar coverage and quality at a lower "
                    f"price -- a reasonable alternative if budget is "
                    f"the main priority."
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
        annual_mileage_km: float | None = None,
        financed_vehicle: bool = False,
        family_usage: bool = False,
        digital_affinity_1to5: int | None = None,
        protection_preference: str | None = None,
        wants_lowest_price: bool = False,
        flood_exposed: bool = False,
        risk_band: str | None = None,
    ) -> dict[str, Any]:
        """
        Same as recommend(), but additionally computes pairwise
        comparison reasons (price, coverage, AND quality
        differentiators) between every pair of the returned top_n
        policies.
        """

        flag_terms, _ = self._parse_coverage_priorities(coverage_priorities)

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
            annual_mileage_km=annual_mileage_km,
            financed_vehicle=financed_vehicle,
            family_usage=family_usage,
            digital_affinity_1to5=digital_affinity_1to5,
            protection_preference=protection_preference,
            wants_lowest_price=wants_lowest_price,
            flood_exposed=flood_exposed,
            risk_band=risk_band,
        )

        recommendations = result["recommendations"]

        comparisons = []

        for i in range(len(recommendations)):
            for j in range(i + 1, len(recommendations)):

                reasons = self._compare_two_policies(
                    recommendations[i],
                    recommendations[j],
                    flag_terms,
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
        annual_mileage_km: float | None = None,
        financed_vehicle: bool = False,
        family_usage: bool = False,
        digital_affinity_1to5: int | None = None,
        protection_preference: str | None = None,
        wants_lowest_price: bool = False,
        flood_exposed: bool = False,
        risk_band: str | None = None,
    ) -> dict[str, Any]:
        """
        Compare two named policies for one customer profile,
        deterministically. Raises KeyError if either policy_id is
        unknown.
        """

        flag_terms, preference_terms = self._parse_coverage_priorities(
            coverage_priorities
        )

        policy_a = self._get_policy_row(policy_id_a)
        policy_b = self._get_policy_row(policy_id_b)

        score_a, premium_a, reasons_a = self._score(
            policy_a, vehicle_idv_rs, ncb_percent, flag_terms,
            preference_terms, budget_sensitivity_1to5, prefers_cashless,
            None, annual_mileage_km, financed_vehicle, family_usage,
            digital_affinity_1to5, protection_preference,
            wants_lowest_price, flood_exposed, risk_band,
        )

        score_b, premium_b, reasons_b = self._score(
            policy_b, vehicle_idv_rs, ncb_percent, flag_terms,
            preference_terms, budget_sensitivity_1to5, prefers_cashless,
            None, annual_mileage_km, financed_vehicle, family_usage,
            digital_affinity_1to5, protection_preference,
            wants_lowest_price, flood_exposed, risk_band,
        )

        matched_a = [c for c in flag_terms if policy_a.get(c)]

        matched_b = [c for c in flag_terms if policy_b.get(c)]

        winner_is_a = score_a >= score_b

        winner_id = policy_id_a if winner_is_a else policy_id_b

        candidate_a = {
            "policy_id": policy_id_a,
            "product_name": policy_a["product_name"],
            "estimated_annual_premium_rs": premium_a,
            "matched_coverage": matched_a,
            "cashless_garage_score": policy_a["cashless_garage_score"],
            "claim_support_score": policy_a["claim_support_score"],
            "digital_servicing_score": policy_a["digital_servicing_score"],
            "service_score": policy_a["service_score"],
        }

        candidate_b = {
            "policy_id": policy_id_b,
            "product_name": policy_b["product_name"],
            "estimated_annual_premium_rs": premium_b,
            "matched_coverage": matched_b,
            "cashless_garage_score": policy_b["cashless_garage_score"],
            "claim_support_score": policy_b["claim_support_score"],
            "digital_servicing_score": policy_b["digital_servicing_score"],
            "service_score": policy_b["service_score"],
        }

        reasons = self._compare_two_policies(candidate_a, candidate_b, flag_terms)

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
                    f"prioritizes lowest price over coverage/quality "
                    f"breadth."
                )

        return {
            "policy_a": {
                "policy_id": policy_id_a,
                "product_name": policy_a["product_name"],
                "suitability_score": score_a,
                "estimated_annual_premium_rs": premium_a,
                "matched_coverage": matched_a,
                "match_reasons": reasons_a,
            },
            "policy_b": {
                "policy_id": policy_id_b,
                "product_name": policy_b["product_name"],
                "suitability_score": score_b,
                "estimated_annual_premium_rs": premium_b,
                "matched_coverage": matched_b,
                "match_reasons": reasons_b,
            },
            "winner_policy_id": winner_id,
            "reasons": reasons,
            "other_better_when": other_better_when,
        }

    @staticmethod
    def _parse_coverage_priorities(
        coverage_priorities: list[str] | None,
    ) -> tuple[list[str], list[str]]:

        coverage_priorities = coverage_priorities or []

        flag_terms = [
            c for c in coverage_priorities if c not in _PREFERENCE_TERMS
        ]

        preference_terms = [
            c for c in coverage_priorities if c in _PREFERENCE_TERMS
        ]

        return flag_terms, preference_terms

    @staticmethod
    def _compare_two_policies(
        rec_a: dict[str, Any],
        rec_b: dict[str, Any],
        flag_terms: list[str],
        max_quality_reasons: int = 2,
    ) -> list[str]:
        """
        The single source of truth for comparing any two scored
        candidates -- used for both top-vs-cheapest and pairwise-
        among-top-N comparisons, so the reasoning is always consistent
        wherever two policies are compared.

        Reports price and coverage-match differences (as before), AND
        the most significant quality-score differentiators (capped at
        `max_quality_reasons`, ranked by how large the gap actually is,
        so the explanation stays focused rather than dumping every
        stat) -- this is what makes a ranking honestly explainable
        when coverage match is tied, which price/coverage alone
        couldn't do.
        """

        reasons: list[str] = []

        premium_a = rec_a["estimated_annual_premium_rs"]

        premium_b = rec_b["estimated_annual_premium_rs"]

        if premium_a != premium_b:

            if premium_a < premium_b:
                cheaper_name, pricier_name = (
                    rec_a["product_name"],
                    rec_b["product_name"],
                )
            else:
                cheaper_name, pricier_name = (
                    rec_b["product_name"],
                    rec_a["product_name"],
                )

            diff = abs(premium_a - premium_b)

            reasons.append(
                f"{cheaper_name} is Rs {diff} cheaper than "
                f"{pricier_name} per year"
            )

        matched_a = len(rec_a["matched_coverage"])

        matched_b = len(rec_b["matched_coverage"])

        if matched_a != matched_b and flag_terms:
            reasons.append(
                f"{rec_a['product_name']} matches {matched_a}/"
                f"{len(flag_terms)} priority coverages vs "
                f"{rec_b['product_name']}'s {matched_b}/"
                f"{len(flag_terms)}"
            )

        quality_diffs = []

        for field, label in _QUALITY_FIELDS:

            diff = rec_a[field] - rec_b[field]

            if abs(diff) >= _QUALITY_DIFF_THRESHOLD:
                quality_diffs.append((abs(diff), field, label, diff))

        quality_diffs.sort(key=lambda item: item[0], reverse=True)

        for _, field, label, diff in quality_diffs[:max_quality_reasons]:

            if diff > 0:
                better_name, worse_name = (
                    rec_a["product_name"],
                    rec_b["product_name"],
                )
                better_score, worse_score = rec_a[field], rec_b[field]
            else:
                better_name, worse_name = (
                    rec_b["product_name"],
                    rec_a["product_name"],
                )
                better_score, worse_score = rec_b[field], rec_a[field]

            reasons.append(
                f"{better_name} has stronger {label} than {worse_name} "
                f"({better_score} vs {worse_score})"
            )

        return reasons

    @staticmethod
    def _is_eligible(
        policy: pd.Series,
        vehicle_age_years: int,
        ev_flag: bool,
        annual_mileage_km: float | None = None,
    ) -> bool:

        max_age = policy.get("target_vehicle_age_max")

        if pd.notna(max_age) and vehicle_age_years > max_age:
            return False

        if policy.get("ev_only") and not ev_flag:
            return False

        max_mileage = policy.get("target_mileage_max")

        if (
            pd.notna(max_mileage)
            and annual_mileage_km is not None
            and annual_mileage_km > max_mileage
        ):
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
        flag_terms: list[str],
        preference_terms: list[str],
        budget_sensitivity_1to5: int,
        prefers_cashless: bool,
        budget_cap_rs: float | None,
        annual_mileage_km: float | None,
        financed_vehicle: bool,
        family_usage: bool,
        digital_affinity_1to5: int | None,
        protection_preference: str | None,
        wants_lowest_price: bool,
        flood_exposed: bool,
        risk_band: str | None,
    ) -> tuple[float, int, list[dict[str, str]]]:

        premium = cls._estimate_premium(
            policy, vehicle_idv, ncb_percent, risk_band, annual_mileage_km
        )

        coverage_fit = (
            sum(1 for c in flag_terms if policy.get(c)) / len(flag_terms)
            if flag_terms
            else 0.0
        )

        effective_prefers_cashless = (
            prefers_cashless or "cashless_strength" in preference_terms
        )

        quality_denominator = 450.0 if effective_prefers_cashless else 400.0

        cashless_weight = 1.5 if effective_prefers_cashless else 1.0

        if digital_affinity_1to5 is None:
            digital_weight = 1.0
        else:
            digital_weight = 0.5 + (digital_affinity_1to5 / 5.0)
            if "digital_servicing" in preference_terms:
                digital_weight *= 1.3

        quality = (
            policy["cashless_garage_score"] * cashless_weight
            + policy["claim_support_score"]
            + policy["digital_servicing_score"] * digital_weight
            + policy["service_score"]
        ) / quality_denominator

        price_weight = budget_sensitivity_1to5 / 5.0

        if protection_preference == "budget_first":
            price_weight = min(1.0, price_weight * 1.5)
        elif protection_preference == "max_protection":
            price_weight = price_weight * 0.4

        effective_wants_lowest_price = (
            wants_lowest_price or "price_control" in preference_terms
        )

        if effective_wants_lowest_price:
            price_weight = min(1.0, price_weight + 0.2)

        over_budget_penalty = 0.0

        if budget_cap_rs is not None and premium > budget_cap_rs:
            over_budget_penalty = min(
                1.0,
                (premium - budget_cap_rs) / budget_cap_rs,
            )

        match_reasons: list[dict[str, str]] = []

        context_bonus = 0.0

        if flood_exposed and policy.get("engine_protect"):
            context_bonus += 15
            match_reasons.append(
                {
                    "coverage": "engine_protect",
                    "reason": (
                        "Engine protection matters for you: your area "
                        "has flood risk"
                    ),
                }
            )

        if financed_vehicle and policy.get("return_to_invoice"):
            context_bonus += 10
            match_reasons.append(
                {
                    "coverage": "return_to_invoice",
                    "reason": (
                        "Return to Invoice matters for you: vehicle "
                        "is financed"
                    ),
                }
            )

        if family_usage and policy.get("passenger_cover"):
            context_bonus += 8
            match_reasons.append(
                {
                    "coverage": "passenger_cover",
                    "reason": "Passenger cover matters for you: family usage",
                }
            )

        if family_usage and policy.get("personal_accident_cover"):
            context_bonus += 8
            match_reasons.append(
                {
                    "coverage": "personal_accident_cover",
                    "reason": (
                        "Personal accident cover matters for you: "
                        "family usage"
                    ),
                }
            )

        score = (
            coverage_fit * 45
            + quality * 35
            + context_bonus
            - price_weight * (premium / 1000) * 0.5
            - over_budget_penalty * 50
        )

        return round(score, 2), premium, match_reasons

    @staticmethod
    def _estimate_premium(
        policy: pd.Series,
        vehicle_idv: float,
        ncb_percent: float,
        risk_band: str | None = None,
        annual_mileage_km: float | None = None,
    ) -> int:

        base = vehicle_idv * policy["base_rate_pct"] + policy["fixed_fee_rs"]

        premium = base * (1 - ncb_percent / 100) * policy["premium_multiplier"]

        if annual_mileage_km is not None and policy.get(
            "low_mileage_discount_pct"
        ):
            premium *= 1 - policy["low_mileage_discount_pct"] / 100

        premium *= _RISK_LOADING.get(risk_band, 1.0)

        return round(premium)