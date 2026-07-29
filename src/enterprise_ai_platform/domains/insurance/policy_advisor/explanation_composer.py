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
    policy and which coverage) that a small model does unreliably --
    confirmed in real testing: reasons got attached to the wrong
    coverage, and even to the wrong policy, despite explicit prompt
    instructions telling it not to. The fix is not a better-worded
    instruction; it's not asking the LLM to do that binding at all.
    Attribution is already 100% known and correct in the structured
    data (PolicyRecommendationEngine computed it); composing it into
    text is pure formatting and belongs in code, matching this
    platform's core principle throughout ("the LLM never decides,
    it only explains"). The LLM's only remaining job, once this
    composer has run, is retelling already-correct text in a warmer
    tone and in Hinglish -- not deciding what connects to what.

    Deliberately NOT metadata-specific or situation-specific: this
    doesn't know or care what a match_reason SAYS, only that it
    belongs to the policy dict it was read from. Works identically
    for any coverage, any reason, any number of policies, without
    needing new code when the underlying metadata grows.
    """

    def compose_policy_paragraph(self, rec: dict[str, Any]) -> str:
        """
        One policy's complete, self-contained paragraph: premium,
        pitch, and every match_reason that belongs to it -- and only
        to it.
        """

        sentences = [
            f"{rec['product_name']} costs Rs "
            f"{rec['estimated_annual_premium_rs']} per year.",
            rec["plain_language_pitch"],
        ]

        for reason in rec.get("match_reasons", []):
            sentences.append(f"{reason}.")

        return " ".join(sentences)

    def compose_recommendation_summary(
        self,
        recommendations_result: dict[str, Any],
    ) -> str:
        """
        The full, ready-to-retell text for a top-N recommendation
        result: one paragraph per policy (each self-contained, no
        cross-policy ambiguity), then the comparison notes (each
        already a complete sentence naming both policies), then any
        why-not-cheapest note.
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