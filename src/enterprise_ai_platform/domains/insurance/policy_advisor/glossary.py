"""
Exact-lookup jargon glossary for Policy Advisor explanations.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class JargonGlossary:
    """
    Looks up insurance jargon by exact term name, loaded from a small
    curated CSV.

    Deliberately NOT retrieved via semantic search, unlike
    regulatory_knowledge -- the caller (Policy Advisor's explanation
    handler) already knows exactly which terms are relevant
    (matched_coverage is a structured list of exact flag names, not
    free text to search over), so a direct dict lookup is both
    simpler and more reliable than embedding similarity for a small,
    precise glossary like this one.
    """

    def __init__(self, glossary_path: Path | str) -> None:

        dataframe = pd.read_csv(glossary_path)

        self._terms: dict[str, tuple[str, str]] = {
            row["term"]: (row["label"], row["definition"])
            for _, row in dataframe.iterrows()
        }

    def lookup(self, term: str) -> tuple[str, str] | None:
        """
        Return (label, definition) for a term, or None if unknown.
        """

        return self._terms.get(term)

    def lookup_many(self, terms: list[str]) -> list[str]:
        """
        Return "Label: definition" strings for every recognized term
        in `terms`, silently skipping unrecognized ones.
        """

        results = []

        for term in terms:

            entry = self.lookup(term)

            if entry is not None:
                label, definition = entry
                results.append(f"{label}: {definition}")

        return results