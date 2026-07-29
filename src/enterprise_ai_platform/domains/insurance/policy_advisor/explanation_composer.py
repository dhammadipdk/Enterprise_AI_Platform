"""
Explanation composer for the Policy Advisor workflow.
"""

from __future__ import annotations

from typing import Any

_RANK_LABELS = ["Best match", "2nd best match", "3rd best match"]


class ExplanationComposer:
    """
    Composes complete, factually-correct English text from
    PolicyRecommendationEngine's structured output -- pure
    deterministic string assembly, no LLM involved.

    This exists because handing an LLM a flat pile of facts,
    match_reasons, and comparison notes for multiple policies at once
    asks it to do ATTRIBUTION work (which reason belongs to which
    policy and which coverage) that a small model does unreliably.
    Attribution is already 100% known and correct in the structured
    data; composing it into text is pure formatting and belongs in
    code, matching this platform's core principle throughout ("the
    LLM never decides, it only explains"). The LLM's only remaining
    job, once this composer has run, is retelling already-correct
    text in a warmer tone and in Hinglish.

    Optionally takes a glossary (JargonGlossary) to look up proper
    display labels for matched coverage that has no specific
    situational reason attached -- reusing the SAME label data
    already curated for jargon explanation, rather than inventing a
    separate humanization scheme for coverage names.
    """

    def __init__(self, glossary: Any | None = None) -> None:

        self._glossary = glossary

    def _humanize_coverage(self, coverage_term: str) -> str:

        if self._glossary is not None:

            entry = self._glossary.lookup(coverage_term)

            if entry is not None:
                label, _definition = entry
                return label

        return coverage_term.replace("_", " ")

    def _join_labels(self, labels: list[str]) -> str:

        if len(labels) == 1:
            return labels[0]

        if len(labels) == 2:
            return f"{labels[0]} and {labels[1]}"

        return ", ".join(labels[:-1]) + f", and {labels[-1]}"

    def compose_policy_paragraph(self, rec: dict[str, Any]) -> str:
        """
        One policy's complete, self-contained paragraph: premium,
        pitch, every match_reason that belongs specifically to it,
        and a plain confirmation of any OTHER matched coverage that
        has no specific situational reason -- so a customer who asked
        for something (e.g. roadside assistance) that simply doesn't
        have a special "why" attached still hears it's included,
        rather than it silently disappearing from the narrative.
        """

        sentences = [
            f"{rec['product_name']} costs Rs "
            f"{rec['estimated_annual_premium_rs']} per year.",
            rec["plain_language_pitch"],
        ]

        reasoned_coverage: set[str] = set()

        for match_reason in rec.get("match_reasons", []):
            sentences.append(f"{match_reason['reason']}.")
            reasoned_coverage.add(match_reason["coverage"])

        remaining_coverage = [
            c
            for c in rec.get("matched_coverage", [])
            if c not in reasoned_coverage
        ]

        if remaining_coverage:
            labels = [self._humanize_coverage(c) for c in remaining_coverage]
            sentences.append(f"It also includes {self._join_labels(labels)}.")

        return " ".join(sentences)

    def compose_recommendation_summary(
        self,
        recommendations_result: dict[str, Any],
    ) -> str:
        """
        The full, ready-to-retell text for a top-N recommendation
        result.
        """

        recommendations = recommendations_result.get("recommendations", [])

        paragraphs = []

        for i, rec in enumerate(recommendations):

            label = (
                _RANK_LABELS[i]
                if i < len(_RANK_LABELS)
                else f"{i + 1}th option"
            )

            paragraphs.append(
                f"{label}: {self.compose_policy_paragraph(rec)}"
            )

        comparisons = recommendations_result.get("comparisons", [])

        comparison_sentences = [
            reason
            for comparison in comparisons
            for reason in comparison["reasons"]
        ]

        full_text = "\n\n".join(paragraphs)

        if comparison_sentences:
            full_text += "\n\nComparing these options: " + " ".join(
                comparison_sentences
            )

        why_not_cheapest = recommendations_result.get("why_not_cheapest")

        if why_not_cheapest:
            full_text += f"\n\n{why_not_cheapest}"

        return full_text

    def compose_comparison_summary(
        self,
        comparison_result: dict[str, Any],
    ) -> str:
        """
        The full, ready-to-retell text for a 1-vs-1 comparison
        result.
        """

        policy_a = comparison_result.get("policy_a", {})

        policy_b = comparison_result.get("policy_b", {})

        winner_id = comparison_result.get("winner_policy_id")

        winner_name = (
            policy_a.get("product_name")
            if winner_id == policy_a.get("policy_id")
            else policy_b.get("product_name")
        )

        text = (
            f"Policy A, {self.compose_policy_paragraph(policy_a)}\n\n"
            f"Policy B, {self.compose_policy_paragraph(policy_b)}\n\n"
            f"The better overall fit for this customer is {winner_name}."
        )

        reasons = comparison_result.get("reasons", [])

        if reasons:
            text += " " + " ".join(reasons) + "."

        other_better_when = comparison_result.get("other_better_when")

        if other_better_when:
            text += f"\n\n{other_better_when}"

        return text