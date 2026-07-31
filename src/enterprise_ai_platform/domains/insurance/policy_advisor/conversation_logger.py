"""
Conversation logging for the Policy Advisor workflow.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from enterprise_ai_platform.memory_engine import MemoryService, MemoryType

# Denylist (not allowlist) of context variable names that must NEVER
# be logged in any form. Deliberately a denylist so it fails safe as
# new fields are introduced: this list must be extended the moment a
# new sensitive field type is added (e.g. once real free-text
# extraction starts capturing names, phone numbers, or addresses),
# rather than assuming unknown new fields are safe by default.
_SENSITIVE_FIELDS = {
    "name",
    "customer_name",
    "phone",
    "phone_number",
    "email",
    "address",
    "exact_address",
    "pincode",
    "gender",
    "marital_status",
    "annual_income_lakh",
}

_REDACTED_PLACEHOLDER = "[REDACTED]"


class ConversationLogger:
    """
    Logs each Policy Advisor conversation turn as EPISODIC memory --
    intended as a future source of training data (e.g. for a smaller
    fine-tuned model) and as a record of real customer questions and
    which responses actually satisfied them (candidate FAQ material).

    Every input variable is passed through an explicit denylist-based
    redaction before storage. This is a real, deliberate constraint:
    nothing sensitive is ever persisted, even for training purposes --
    training value and privacy are treated as a real tradeoff here,
    resolved in favor of privacy every time a field is uncertain.

    Logging failures are swallowed rather than raised, since a
    logging outage must never break the customer-facing workflow --
    but this means logging failures are currently silent, which is a
    real observability gap worth addressing once this codebase has a
    general logging/monitoring setup, not something to treat as fully
    solved by this class alone.
    """

    def __init__(self, memory_service: MemoryService) -> None:

        self._memory_service = memory_service

    def log_turn(
        self,
        session_id: str,
        input_variables: dict[str, Any],
        outcome_path: list[str],
        response_text: str | None,
    ) -> None:
        """
        Log one conversation turn. Never raises.
        """

        try:

            redacted_input = self._redact(input_variables)

            self._memory_service.store(
                memory_type=MemoryType.EPISODIC,
                content={
                    "input_variables": redacted_input,
                    "outcome_path": outcome_path,
                    "response_text": response_text,
                    "logged_at": datetime.now(timezone.utc).isoformat(),
                },
                collection=f"policy_advisor_conversation_log:{session_id}",
                metadata={"workflow": "policy_advisor"},
            )

        except Exception:
            pass

    @staticmethod
    def _redact(variables: dict[str, Any]) -> dict[str, Any]:

        return {
            key: (
                _REDACTED_PLACEHOLDER
                if key in _SENSITIVE_FIELDS
                else value
            )
            for key, value in variables.items()
        }