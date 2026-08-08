"""
Vehicle category classification for the Policy Advisor workflow.
"""

from __future__ import annotations

_VEHICLE_CATEGORY_KEYWORDS = {
    "two_wheeler": {
        "bike", "motorcycle", "motorbike", "scooter", "scooty",
        "two-wheeler", "two wheeler", "moped",
    },
    "commercial_vehicle": {
        "truck", "lorry", "bus", "commercial vehicle",
        "auto rickshaw", "tempo", "tractor",
    },
}


def classify_vehicle_category(vehicle_segment: str | None) -> str:
    """
    Deterministic classifier: normalizes free-text vehicle_segment
    into a canonical vehicle_category -- "car", "two_wheeler", or
    "commercial_vehicle". This is a categorization framework for the
    whole motor domain, NOT a decline mechanism: the catalog now
    contains real bike and commercial-vehicle products alongside
    cars, and this classifier is what routes a customer's profile to
    the right subset.

    Defaults to "car" for anything not explicitly matching a known
    two-wheeler/commercial keyword -- covers car model names ("Maruti
    Swift"), body styles ("SUV", "Sedan"), and unset/unknown values,
    matching InsureAI's primary customer base (used-car buyers).
    Verified conservative: never misclassifies a car model or body
    style as a non-car category.

    Deliberately independent of EV-ness (ev_flag) -- an EV bike is
    vehicle_category="two_wheeler" AND ev_flag=True, two orthogonal
    facts, not a single combined category. This mirrors how EV cars
    already work via the separate ev_only catalog flag.
    """

    if vehicle_segment is None:
        return "car"

    segment_lower = vehicle_segment.lower()

    for category, keywords in _VEHICLE_CATEGORY_KEYWORDS.items():
        if any(keyword in segment_lower for keyword in keywords):
            return category

    return "car"