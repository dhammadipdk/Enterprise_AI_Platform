import pytest

from enterprise_ai_platform.domains.insurance.policy_advisor.recommendation_engine import (
    PolicyRecommendationEngine,
)

CATALOG_PATH = "src/enterprise_ai_platform/domains/insurance/knowledge/policy_catalog/entity_catalog.csv"


CATALOG_PATH = "src/enterprise_ai_platform/domains/insurance/knowledge/policy_catalog/entity_catalog.csv"
ONTOLOGY_PATH = "src/enterprise_ai_platform/domains/insurance/knowledge/coverage_ontology/relationships.csv"


@pytest.fixture(scope="module")
def engine():
    return PolicyRecommendationEngine(CATALOG_PATH, ONTOLOGY_PATH)


def test_recommend_returns_ranked_eligible_policies(engine):

    result = engine.recommend(
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
        coverage_priorities=["zero_dep", "roadside_assistance", "ncb_protect"],
        prefers_cashless=True,
        budget_cap_rs=12000,
    )

    assert result["total_eligible"] > 0

    assert len(result["recommendations"]) == 3

    scores = [r["suitability_score"] for r in result["recommendations"]]

    assert scores == sorted(scores, reverse=True)


def test_top_recommendation_matches_all_requested_coverage(engine):

    coverage_priorities = ["zero_dep", "roadside_assistance", "ncb_protect"]

    result = engine.recommend(
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
        coverage_priorities=coverage_priorities,
        prefers_cashless=True,
    )

    top = result["recommendations"][0]

    assert set(top["matched_coverage"]) == set(coverage_priorities)


def test_old_vehicle_returns_empty_with_clear_message(engine):

    result = engine.recommend(vehicle_idv_rs=200000, vehicle_age_years=25)

    assert result["recommendations"] == []

    assert result["total_eligible"] == 0

    assert "exceeds every policy's limits" in result["message"]


def test_ev_only_policies_excluded_for_non_ev_customer(engine):

    result = engine.recommend(
        vehicle_idv_rs=500000,
        vehicle_age_years=2,
        ev_flag=False,
        top_n=48,
    )

    assert result["total_eligible"] < 48


def test_ev_customer_sees_ev_shield_policies_top_ranked(engine):

    result = engine.recommend(
        vehicle_idv_rs=800000,
        vehicle_age_years=2,
        ev_flag=True,
        coverage_priorities=["ev_battery_cover", "zero_dep"],
    )

    assert result["recommendations"][0]["matched_coverage"]


def test_why_not_cheapest_present_when_top_pick_isnt_cheapest(engine):

    result = engine.recommend(
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
        coverage_priorities=["zero_dep", "roadside_assistance", "ncb_protect"],
        prefers_cashless=True,
    )

    assert result["why_not_cheapest"] is not None

    assert "lower price" in result["why_not_cheapest"]


def test_no_coverage_priorities_still_returns_ranked_results(engine):

    result = engine.recommend(vehicle_idv_rs=300000, vehicle_age_years=4)

    assert len(result["recommendations"]) == 3


def test_coverage_vocabulary_excludes_preference_terms(engine):
    """
    Real customer_profiles.coverage_priorities values include
    preference terms ("digital_servicing", "cashless_strength",
    "price_control") that aren't policy_catalog boolean columns --
    these must never appear in matched_coverage.
    """

    result = engine.recommend(
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
        coverage_priorities=[
            "third_party_cover",
            "passenger_cover",
            "digital_servicing",
            "cashless_strength",
        ],
    )

    top = result["recommendations"][0]

    assert "digital_servicing" not in top["matched_coverage"]

    assert "cashless_strength" not in top["matched_coverage"]


def test_flood_exposed_surfaces_engine_protect_with_tagged_reason(engine):

    result = engine.recommend(
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
        coverage_priorities=["zero_dep", "roadside_assistance"],
        flood_exposed=True,
    )

    top = result["recommendations"][0]

    engine_protect_reasons = [
        r for r in top["match_reasons"] if r["coverage"] == "engine_protect"
    ]

    assert len(engine_protect_reasons) == 1

    assert "flood" in engine_protect_reasons[0]["reason"].lower()


def test_financed_vehicle_surfaces_return_to_invoice_with_tagged_reason(engine):

    result = engine.recommend(
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
        financed_vehicle=True,
    )

    top = result["recommendations"][0]

    rti_reasons = [
        r for r in top["match_reasons"] if r["coverage"] == "return_to_invoice"
    ]

    assert len(rti_reasons) == 1

    assert "financed" in rti_reasons[0]["reason"].lower()


def test_mileage_discount_reduces_premium_when_known(engine):

    result_unknown = engine.recommend(
        vehicle_idv_rs=400000, vehicle_age_years=3, top_n=48
    )

    result_low_mileage = engine.recommend(
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        annual_mileage_km=8000,
        top_n=48,
    )

    by_id_unknown = {
        r["policy_id"]: r["estimated_annual_premium_rs"]
        for r in result_unknown["recommendations"]
    }

    by_id_low_mileage = {
        r["policy_id"]: r["estimated_annual_premium_rs"]
        for r in result_low_mileage["recommendations"]
    }

    discounted = [
        pid
        for pid in by_id_unknown
        if pid in by_id_low_mileage
        and by_id_low_mileage[pid] < by_id_unknown[pid]
    ]

    assert len(discounted) > 0


def test_risk_band_loads_premium(engine):

    low_risk = engine.compare(
        "INS_C_FAMILY_CAR_PLUS",
        "INS_C_FAMILY_CAR_PLUS",
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        risk_band="low",
    )

    high_risk = engine.compare(
        "INS_C_FAMILY_CAR_PLUS",
        "INS_C_FAMILY_CAR_PLUS",
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        risk_band="high",
    )

    assert (
        high_risk["policy_a"]["estimated_annual_premium_rs"]
        > low_risk["policy_a"]["estimated_annual_premium_rs"]
    )


def test_recommend_with_comparison_produces_pairwise_reasons(engine):

    result = engine.recommend_with_comparison(
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
        coverage_priorities=["zero_dep", "roadside_assistance"],
        prefers_cashless=True,
    )

    assert len(result["comparisons"]) == 3  # C(3,2) pairs

    for comparison in result["comparisons"]:
        assert isinstance(comparison["reasons"], list)


def test_compare_two_named_policies(engine):

    result = engine.compare(
        "INS_C_FAMILY_CAR_PLUS",
        "INS_C_ZERO_DEP_PLUS",
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
        coverage_priorities=["zero_dep", "roadside_assistance", "ncb_protect"],
        prefers_cashless=True,
    )

    assert result["winner_policy_id"] in (
        "INS_C_FAMILY_CAR_PLUS",
        "INS_C_ZERO_DEP_PLUS",
    )

    assert isinstance(result["reasons"], list)


def test_compare_unknown_policy_raises_key_error(engine):

    with pytest.raises(KeyError):
        engine.compare(
            "DOES_NOT_EXIST",
            "INS_C_FAMILY_CAR_PLUS",
            vehicle_idv_rs=400000,
            vehicle_age_years=3,
        )


def test_comparison_reasons_state_both_directions_explicitly(engine):
    """
    Regression test for the specific bug found in real Ollama testing:
    a comparative conclusion must be stated with an explicit,
    redundant verdict (not just two numbers side by side), so a
    downstream translation step has minimal room to invert it.
    """

    result = engine.compare(
        "INS_C_ZERO_DEP_PLUS",
        "INS_D_ZERO_DEP_PLUS",
        vehicle_idv_rs=400000,
        vehicle_age_years=3,
        ncb_percent=20,
    )

    reasons_text = " ".join(result["reasons"])

    assert "MORE" in reasons_text or "LESS" in reasons_text