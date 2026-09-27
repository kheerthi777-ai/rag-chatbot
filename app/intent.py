"""Sort a question before any search or answer is attempted."""

from __future__ import annotations

import re
from dataclasses import dataclass

PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
AADHAAR = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
PHONE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}\b")
LONG_DIGITS = re.compile(r"\b\d{9,}\b")
OTP = re.compile(r"\botp\b", re.IGNORECASE)

ADVICE = re.compile(
    r"\b(should i|buy|sell|hold|recommend|portfolio|allocate)\b|invest in|which is better",
    re.IGNORECASE,
)
RETURNS = re.compile(
    r"\bcagr\b|\breturns?\b|\balpha\b|\d+\s*-?\s*years?\b|nav performance|compare performance|highest return",
    re.IGNORECASE,
)

SCHEME_RULES = (
    (("elss", "tax saver"), "hdfc-elss"),
    (("small cap",), "hdfc-small-cap"),
    (("large cap",), "hdfc-large-cap"),
    (("flexi", "flexicap", "equity fund"), "hdfc-flexi-cap"),
    (("balanced advantage", "balanced-advantage"), "hdfc-balanced-advantage"),
)


@dataclass(frozen=True)
class Intent:
    kind: str
    scheme_id: str | None


def classify(question: str) -> Intent:
    scheme_id = detect_scheme(question)
    if _is_pii(question):
        return Intent("pii", None)
    if ADVICE.search(question):
        return Intent("advice", scheme_id)
    if RETURNS.search(question):
        return Intent("returns", scheme_id)
    return Intent("factual", scheme_id)


def detect_scheme(question: str) -> str | None:
    lowered = question.lower()
    found: list[str] = []
    for keys, scheme_id in SCHEME_RULES:
        if any(key in lowered for key in keys):
            found.append(scheme_id)
    if len(found) == 1:
        return found[0]
    return None


def _is_pii(question: str) -> bool:
    return any(
        pattern.search(question)
        for pattern in (PAN, AADHAAR, EMAIL, PHONE, LONG_DIGITS, OTP)
    )
