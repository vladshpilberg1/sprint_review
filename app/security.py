"""Security checkpoint — PII scrubbing and prompt-injection defence.

This module runs **before** any user-supplied text reaches an LLM agent or
gets written to logs.  It is pure-Python (regex-based) with zero external
dependencies so it adds no latency and no API cost.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# PII patterns
# ---------------------------------------------------------------------------

# Order matters: more specific patterns first to avoid partial matches.

_PII_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    # ── Email addresses ───────────────────────────────────────────────────
    (
        "email",
        re.compile(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        ),
        "[EMAIL_REDACTED]",
    ),
    # ── Employee IDs  (EMP-12345, E12345, EMP12345, emp-00042, …) ─────
    (
        "employee_id",
        re.compile(
            r"\bE(?:MP)?[-\s]?\d{4,6}\b",
            re.IGNORECASE,
        ),
        "[EMPLOYEE_ID_REDACTED]",
    ),
    # ── SSNs  (123-45-6789 or 123 45 6789) ────────────────────────────
    (
        "ssn",
        re.compile(
            r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b",
        ),
        "[SSN_REDACTED]",
    ),
    # ── Credit-card numbers ───────────────────────────────────────────────
    # 13–19 digits optionally separated by dashes or spaces (in groups of 4).
    (
        "credit_card",
        re.compile(
            r"\b(?:\d[-\s]?){12,18}\d\b",
        ),
        "[CC_REDACTED]",
    ),
]


def scrub_pii(text: str) -> tuple[str, list[str]]:
    """Replace PII tokens in *text* with safe placeholders.

    Returns:
        A ``(scrubbed_text, categories)`` tuple where *categories* lists the
        PII types that were found (e.g. ``["email", "ssn"]``).
    """
    categories_found: list[str] = []
    for category, pattern, placeholder in _PII_PATTERNS:
        if pattern.search(text):
            text = pattern.sub(placeholder, text)
            if category not in categories_found:
                categories_found.append(category)
    return text, categories_found


# ---------------------------------------------------------------------------
# Prompt-injection detection
# ---------------------------------------------------------------------------

# Case-insensitive phrases that strongly signal an injection attempt.
_INJECTION_PHRASES: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+(all\s+)?above\s+instructions",
        r"disregard\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?above\s+instructions",
        r"forget\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+a\b",
        r"you\s+are\s+now\s+an\b",
        r"act\s+as\s+if\s+you\s+are\b",
        r"pretend\s+you\s+are\b",
        r"\bsystem\s*:",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\bASSISTANT\s*:",
        r"\bUSER\s*:",
        r"###\s*Instruction",
        r"###\s*System",
        r"\[INST\]",
        r"\[/INST\]",
        r"<\s*system\s*>",
        r"</\s*system\s*>",
        r"do\s+not\s+follow\s+(your|the)\s+instructions",
        r"override\s+(your|the)\s+(previous\s+)?instructions",
        r"new\s+instructions?\s*:",
        r"from\s+now\s+on\s*,?\s*(you\s+are|ignore|forget)",
    ]
]


def detect_prompt_injection(text: str) -> tuple[str, bool]:
    """Scan *text* for prompt-injection attempts.

    If injection markers are found they are stripped from the text.

    Returns:
        A ``(cleaned_text, was_injected)`` tuple.
    """
    detected = False
    for pattern in _INJECTION_PHRASES:
        if pattern.search(text):
            detected = True
            text = pattern.sub("", text)

    # Collapse any whitespace runs left by stripping.
    if detected:
        text = re.sub(r"[ \t]{2,}", " ", text).strip()

    return text, detected


# ---------------------------------------------------------------------------
# Combined convenience wrapper
# ---------------------------------------------------------------------------


def sanitize(text: str) -> tuple[str, dict]:
    """Run the full security pipeline: PII scrubbing → injection defence.

    Returns:
        A ``(clean_text, report)`` tuple where *report* is::

            {
                "pii_categories_redacted": ["email", ...],
                "prompt_injection_detected": True | False,
            }
    """
    text, pii_cats = scrub_pii(text)
    text, injected = detect_prompt_injection(text)
    report = {
        "pii_categories_redacted": pii_cats,
        "prompt_injection_detected": injected,
    }
    return text, report
