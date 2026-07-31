"""
Deterministic city-risk lookup for the Policy Advisor workflow.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

_NON_CITY_ROWS = {"tier2", "tier3"}


class LocationRiskReference:
    """
    Deterministic, exact lookup of city-level flood/theft/traffic risk
    -- NOT an LLM inference, NOT RAG. A customer naming a real city is
    a structured, exact-match fact, so a direct substring match
    against a small reference table is more reliable than asking a
    model to recall or infer geographic risk classifications --
    confirmed necessary in real testing: a model correctly extracted
    other fields from the same message but consistently omitted
    flood_risk_band even when a well-known flood-prone city was named
    explicitly.
    """

    def __init__(self, reference_path: Path | str) -> None:

        self._table = pd.read_csv(reference_path)

    def match_city(self, message: str) -> dict[str, Any] | None:
        """
        Return the matching row's data if a known city is named
        (word-boundary aware substring match), else None.
        """

        message_lower = message.lower()

        for _, row in self._table.iterrows():

            city = row["city"]

            if city.lower() in _NON_CITY_ROWS:
                continue

            if re.search(rf"\b{re.escape(city.lower())}\b", message_lower):

                return {
                    "city": city,
                    "flood_risk": row["flood_risk"],
                    "theft_risk": row["theft_risk"],
                    "traffic_risk": row["traffic_risk"],
                    "addon_priority": row["addon_priority"],
                }

        return None