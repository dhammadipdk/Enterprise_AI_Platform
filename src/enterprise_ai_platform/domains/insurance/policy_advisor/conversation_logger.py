"""
Conversation logging for the Policy Advisor workflow.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from enterprise_ai_platform.memory_engine import MemoryService, MemoryType

from enterprise_ai_platform.domains.insurance.policy_advisor.text_redaction import (
    redact_raw_message,
)

_SENSITIVE_FIELDS = {
    "name",
    "customer_name",
    "phone",
    "phone_number",
    "mobile_number",
    "email",
    "email_address",
    "address",
    "exact_address",
    "residential_address",
    "pincode",
    "gender",
    "marital_status",
    "annual_income_lakh",
    "date_of_birth",  # confirmed "Sensitive Personal" in canonical_schema.csv
    "vehicle_registration_number",  # confirmed "Sensitive Personal", Vehicle domain
    "vin",
    "engine_number",
    "chassis_number",
    # NOTE: "age" is deliberately NOT here -- confirmed "Internal"
    # classification (not Personal/Sensitive Personal) in the real
    # Customer domain canonical_schema.csv, not my own assumption.
}

_REDACTED_PLACEHOLDER = "[REDACTED]"


class ConversationLogger:
    """
    Logs each Policy Advisor conversation turn as EPISODIC memory --
    a historical record of individual events (contrast with the
    customer profile in extraction_handler, stored as SEMANTIC --
    durable facts, not a record of what happened when).

    Intended as future training data (e.g. for a smaller fine-tuned
    model, or reinforcement-learning-style quality improvement) and
    as a source of real customer-need patterns. Both the structured
    input variables AND the raw customer message (redacted) are
    logged, since training on communication quality needs to see
    what the customer actually said, not just what got extracted from
    it.

    Every input variable and the raw message both go through explicit
    redaction before storage -- training value and privacy are a real
    tradeoff here, resolved in favor of privacy whenever a field is
    uncertain.
    """

    def __init__(self, memory_service: MemoryService) -> None:

        self._memory_service = memory_service

    def log_turn(
        self,
        session_id: str,
        input_variables: dict[str, Any],
        outcome_path: list[str],
        response_text: str | None,
        raw_customer_message: str | None = None,
        extracted_name: str | None = None,
    ) -> None:
        """
        Log one conversation turn. Never raises.
        """

        try:

            redacted_input = self._redact_variables(input_variables)

            redacted_message = (
                redact_raw_message(raw_customer_message, extracted_name)
                if raw_customer_message is not None
                else None
            )

            self._memory_service.store(
                memory_type=MemoryType.EPISODIC,
                content={
                    "input_variables": redacted_input,
                    "raw_customer_message_redacted": redacted_message,
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
    def _redact_variables(variables: dict[str, Any]) -> dict[str, Any]:

        return {
            key: (
                _REDACTED_PLACEHOLDER
                if key in _SENSITIVE_FIELDS
                else value
            )
            for key, value in variables.items()
        }