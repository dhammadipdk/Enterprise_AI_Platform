from enterprise_ai_platform.domains.insurance.policy_advisor.risk_scoring_engine import (
    RiskScoringEngine,
)


def test_no_factors_gives_low_baseline() -> None:

    engine = RiskScoringEngine()

    result = engine.score()

    assert result["risk_band"] == "low"

    assert result["risk_factors"] == []

    assert result["flood_exposed"] is False

    assert result["theft_exposed"] is False


def test_flood_prone_residence_sets_flood_exposed() -> None:

    engine = RiskScoringEngine()

    result = engine.score(residence_cluster="coastal_flood_prone")

    assert result["flood_exposed"] is True

    assert any("flood" in f.lower() for f in result["risk_factors"])


def test_claims_and_at_fault_do_not_fully_double_count() -> None:

    engine = RiskScoringEngine()

    claims_only = engine.score(previous_claims_3yr=2)

    claims_plus_at_fault = engine.score(previous_claims_3yr=2, at_fault_claims_3yr=2)

    # at_fault should add SOME extra weight, but nowhere near doubling
    # the claims-only score (confirms it's incremental, not independent)
    claims_delta = claims_only["risk_score"] - 28

    combined_delta = claims_plus_at_fault["risk_score"] - 28

    assert combined_delta > claims_delta

    assert combined_delta < claims_delta * 2


def test_parking_type_alone_does_not_push_low_risk_to_medium() -> None:

    engine = RiskScoringEngine()

    result = engine.score(parking_type="open_lot")

    assert result["risk_band"] == "low"


def test_theft_history_plus_risky_parking_compounds() -> None:

    engine = RiskScoringEngine()

    parking_alone = engine.score(parking_type="street")

    parking_with_theft_history = engine.score(
        parking_type="street", theft_history=1
    )

    assert (
        parking_with_theft_history["risk_score"] > parking_alone["risk_score"]
    )

    assert parking_with_theft_history["theft_exposed"] is True


def test_anti_theft_and_adas_reduce_score() -> None:

    engine = RiskScoringEngine()

    baseline = engine.score(theft_history=1)

    with_mitigations = engine.score(
        theft_history=1, anti_theft_device=True, adas_level=2
    )

    assert with_mitigations["risk_score"] < baseline["risk_score"]


def test_high_risk_combination_reaches_high_band() -> None:

    engine = RiskScoringEngine()

    result = engine.score(
        residence_cluster="metro_high_theft",
        city_risk_band="high",
        previous_claims_3yr=3,
        at_fault_claims_3yr=2,
        theft_history=1,
        traffic_violations_3yr=2,
        driving_experience_years=1,
    )

    assert result["risk_band"] == "high"


def test_score_stays_within_0_to_100_bounds() -> None:

    engine = RiskScoringEngine()

    result = engine.score(
        residence_cluster="metro_high_theft",
        city_risk_band="high",
        flood_risk_band="high",
        previous_claims_3yr=10,
        at_fault_claims_3yr=10,
        theft_history=10,
        traffic_violations_3yr=10,
        parking_type="street",
        driving_experience_years=0,
        annual_mileage_km=50000,
        age=70,
        commute_pattern="long_distance",
    )

    assert 0 <= result["risk_score"] <= 100