"""
Ontology-driven coverage reasoning for the Policy Advisor workflow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

# Ontology target concepts that map directly to a real policy_catalog
# boolean column. Verified against the real catalog before use --
# several ontology-actionable concepts (charger_cover, tyre_protection,
# key_replacement, daily_allowance, strong_claim_support,
# strong_theft_protection, premium_plans, value_plans, ...) have NO
# matching catalog column and are deliberately left unmapped rather
# than guessed at -- they're either already handled by existing
# mechanisms (quality-score weighting, price_weight/protection_
# preference) or not yet actionable at all. Confirmed against
# reference_data/insurance/addon_cover_types.csv: TYRE_PROTECT,
# KEY_REPLACEMENT, DAILY_ALLOWANCE, LOSS_OF_PERSONAL_BELONGINGS are
# officially recognized add-on types with no policy_catalog column
# yet -- a real catalog gap, not a mapping mistake.
_ONTOLOGY_TO_CATALOG_FLAG = {
    "engine_protect": "engine_protect",
    "zero_depreciation": "zero_dep",
    "return_to_invoice": "return_to_invoice",
    "roadside_assistance": "roadside_assistance",
    "passenger_cover": "passenger_cover",
    "battery_cover": "ev_battery_cover",
    "consumables_cover": "consumables_cover",
    "ncb_protection": "ncb_protect",
    "personal_accident_cover": "personal_accident_cover",
    "own_damage_cover": "own_damage_cover",
    "third_party_cover": "third_party_cover",
    "telematics_required": "telematics_required",
}

_TRAIT_LABELS = {
    "flood_risk": "your area has flood risk",
    "theft_risk": "your area has elevated theft risk",
    "high_theft_zone": "your area has high theft rates",
    "new_vehicle": "your vehicle is new",
    "high_mileage": "you drive high annual mileage",
    "highway_driving": "you do a lot of highway/long-distance driving",
    "family_usage": "this is a family-usage vehicle",
    "family_user": "this is a family-usage vehicle",
    "ev_vehicle": "your vehicle is electric",
    "luxury_car": "your vehicle has a high insured value",
    "senior_driver": "your age profile",
}

_ACTIONABLE_RELATIONSHIPS = {"requires", "benefits_from", "recommends"}

_BONUS_PER_MATCH = 12


class CoverageOntology:
    """
    Loads the real ontology_relationships.csv (source_entity,
    relationship, target_entity triples -- e.g. "flood_risk requires
    engine_protect", "family_usage benefits_from passenger_cover")
    and matches it against a customer's derived traits, deterministically.

    Replaces what used to be individually hardcoded if/else branches
    in PolicyRecommendationEngine._score() (one Python condition per
    trait -- flood, financed, family) with a single generic engine
    that works against ANY trait/coverage rule already present in the
    ontology, including several this codebase never explicitly
    modeled before (new_vehicle -> zero_dep/return_to_invoice,
    high_mileage -> roadside_assistance, highway_driving ->
    roadside_assistance). Adding a new rule later means adding a row
    to the CSV, not writing new Python.

    This ontology is sourced from the platform's Contextual
    Intelligence repository (knowledge/ root, not the Business Domain
    schema layer) -- it is a first-pass draft, not yet aligned with
    the more formally specified Coverage domain canonical_schema
    (which defines a "Coverage Relationship" entity for exactly this
    purpose but has no populated instance data yet). Treat this the
    same way as the rest of the synthetic dataset: good enough to
    build and test against now, worth revisiting once a more
    authoritative version exists.

    This is a DETERMINISTIC LOOKUP, not RAG/semantic search -- the
    ontology is small, structured, exact-match data (like
    policy_catalog itself), and semantic similarity search would add
    retrieval risk to something that's a clean, exact join. RAG
    (KnowledgeService.hybrid_search) remains reserved for genuinely
    unstructured prose (regulatory_knowledge, jargon definitions),
    where there's no clean structured key to look up by instead.
    """

    def __init__(self, ontology_path: Path | str) -> None:

        self._ontology = pd.read_csv(ontology_path)

    def find_matches(
        self,
        active_traits: list[str],
    ) -> dict[str, list[str]]:
        """
        Returns {catalog_flag: [reason_labels]} -- one entry per
        UNIQUE catalog flag any active trait points to, with every
        distinct contributing reason combined under it (not stacked
        as separate bonuses) -- e.g. if both high_mileage and
        highway_driving point to roadside_assistance, that appears
        once, with both reasons listed, not as two separate bonuses.
        """

        if not active_traits:
            return {}

        matches = self._ontology[
            self._ontology["source_entity"].isin(active_traits)
            & self._ontology["relationship"].isin(_ACTIONABLE_RELATIONSHIPS)
        ]

        grouped: dict[str, list[str]] = {}

        for _, row in matches.iterrows():

            catalog_flag = _ONTOLOGY_TO_CATALOG_FLAG.get(row["target_entity"])

            if not catalog_flag:
                continue

            label = _TRAIT_LABELS.get(row["source_entity"], row["source_entity"])

            grouped.setdefault(catalog_flag, [])

            if label not in grouped[catalog_flag]:
                grouped[catalog_flag].append(label)

        return grouped


def derive_active_traits(
    vehicle_age_years: int | None = None,
    annual_mileage_km: float | None = None,
    commute_pattern: str | None = None,
    family_usage: bool = False,
    ev_flag: bool = False,
    flood_exposed: bool = False,
    theft_exposed: bool = False,
    vehicle_idv_rs: float | None = None,
    age: int | None = None,
) -> list[str]:
    """
    Map a customer's profile fields to ontology source_entity trait
    names. Thresholds here (2 years for "new", 20000km for "high
    mileage", Rs 15 lakh for "luxury", age 60 for "senior") are
    reasonable, stated defaults -- not sourced from a specific
    document -- worth revisiting once real usage data exists to
    calibrate against, same caveat as RiskScoringEngine's weights.
    """

    traits: list[str] = []

    if flood_exposed:
        traits.append("flood_risk")

    if theft_exposed:
        traits.append("theft_risk")

    if vehicle_age_years is not None and vehicle_age_years <= 2:
        traits.append("new_vehicle")

    if annual_mileage_km is not None and annual_mileage_km > 20000:
        traits.append("high_mileage")

    if commute_pattern == "long_distance":
        traits.append("highway_driving")

    if family_usage:
        traits.append("family_usage")

    if ev_flag:
        traits.append("ev_vehicle")

    if vehicle_idv_rs is not None and vehicle_idv_rs > 1_500_000:
        traits.append("luxury_car")

    if age is not None and age > 60:
        traits.append("senior_driver")

    return traits


def apply_ontology_bonus(
    policy: pd.Series,
    ontology: CoverageOntology,
    active_traits: list[str],
    bonus_per_match: int = _BONUS_PER_MATCH,
) -> tuple[float, list[dict[str, str]]]:
    """
    Apply the ontology's matched bonuses to one policy. Returns
    (total_bonus, match_reasons) -- match_reasons already in the same
    {"coverage": ..., "reason": ...} shape
    PolicyRecommendationEngine._score() has always used.
    """

    grouped = ontology.find_matches(active_traits)

    total_bonus = 0.0

    match_reasons: list[dict[str, str]] = []

    for catalog_flag, reason_labels in grouped.items():

        if not policy.get(catalog_flag):
            continue

        total_bonus += bonus_per_match

        combined_reason = " and ".join(reason_labels)

        display_label = catalog_flag.replace("_", " ")

        match_reasons.append(
            {
                "coverage": catalog_flag,
                "reason": f"{display_label} matters for you: {combined_reason}",
            }
        )

    return total_bonus, match_reasons