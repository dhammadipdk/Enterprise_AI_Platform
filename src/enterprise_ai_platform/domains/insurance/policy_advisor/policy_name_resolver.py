"""
Deterministic policy name resolution for the Policy Advisor workflow.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class PolicyNameResolver:
    """
    Resolves free-text policy name mentions (e.g. "ClaimEase
    ThirdParty", a partial/informal name a customer would actually
    type) against real catalog product_name values -- deterministic
    word-overlap matching, not an LLM guess, for the same reason
    city/coverage lookups are deterministic: which specific policy a
    customer means isn't something to leave to model recall.

    Prefers matching against a customer's own last-shown policy list
    (if given) before falling back to the full catalog: a customer
    referencing "DriveWise" after being shown 3 specific options
    almost certainly means the DriveWise option among THOSE 3, not
    any DriveWise product anywhere in the catalog. Within a narrow
    candidate pool, one distinguishing word is enough; against the
    full catalog, at least two overlapping words are required to
    avoid a common single word ("Plus", "Basic") matching too widely.
    Either way, a genuinely ambiguous match (best and second-best
    candidate tie) returns None rather than guessing.
    """

    def __init__(self, catalog_path: Path | str) -> None:

        self._catalog = pd.read_csv(catalog_path)

    def resolve(
        self,
        mentioned_name: str | None,
        candidate_policy_ids: list[str] | None = None,
    ) -> str | None:

        if not mentioned_name:
            return None

        if candidate_policy_ids:

            restricted = self._catalog[
                self._catalog["policy_id"].isin(candidate_policy_ids)
            ]

            if not restricted.empty:

                match = self._best_match(mentioned_name, restricted, min_overlap=1)

                if match is not None:
                    return match

        return self._best_match(mentioned_name, self._catalog, min_overlap=2)

    @staticmethod
    def _best_match(
        mentioned_name: str,
        pool: pd.DataFrame,
        min_overlap: int,
    ) -> str | None:

        mentioned_words = set(mentioned_name.lower().split())

        best_policy_id = None

        best_score = 0

        second_best_score = 0

        for _, row in pool.iterrows():

            product_words = set(row["product_name"].lower().split())

            overlap = len(mentioned_words & product_words)

            if overlap > best_score:
                second_best_score = best_score
                best_score = overlap
                best_policy_id = row["policy_id"]
            elif overlap > second_best_score:
                second_best_score = overlap

        if best_score >= min_overlap and best_score > second_best_score:
            return best_policy_id

        return None