"""
Raw free-text PII redaction for conversation logging.
"""

from __future__ import annotations

import re

_PHONE_PATTERN = re.compile(r"\b\d{10}\b|\+91[\s-]?\d{10}\b")

_EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def redact_raw_message(message: str, extracted_name: str | None = None) -> str:
    """
    Redact PII from a raw customer message before it is ever logged.

    Two layers, deliberately combined rather than relying on either
    alone: (1) if the extraction step already identified a name, that
    exact string is scrubbed out of the raw text too -- a name pulled
    into a structured field is still sitting in the original sentence
    otherwise; (2) a deterministic regex backstop for common
    structured PII patterns (phone numbers, emails) that the
    extraction schema was never asked to capture at all, so nothing
    relies solely on the LLM extraction step correctly noticing them.

    Not a complete PII detector -- addresses, or names the extraction
    step didn't catch, could still leak through. Treated as a strong
    first layer, not a guarantee, and worth revisiting if real
    conversation volume surfaces gaps.
    """

    redacted = message

    if extracted_name:
        redacted = re.sub(
            re.escape(extracted_name),
            "[REDACTED]",
            redacted,
            flags=re.IGNORECASE,
        )

    redacted = _PHONE_PATTERN.sub("[REDACTED]", redacted)

    redacted = _EMAIL_PATTERN.sub("[REDACTED]", redacted)

    return redacted