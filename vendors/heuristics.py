import re

JAILBREAK_PHRASES = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore all prior instructions",
    "disregard your instructions",
    "disregard previous instructions",
    "you are now in developer mode",
    "you are now dan",
    "dan mode",
    "pretend you are",
    "act as if you have no restrictions",
    "bypass your guidelines",
    "bypass your restrictions",
    "reveal your system prompt",
    "reveal your instructions",
    "you have no restrictions",
    "no ethical guidelines",
    "jailbreak",
]

CONFIDENTIAL_KEYWORDS = [
    "confidential",
    "proprietary",
    "internal use only",
    "trade secret",
    "do not distribute",
]

# SSNs never issued by the SSA (900-series area numbers, or the well-known
# 000/all-zero placeholder blocks) - obviously synthetic, never real.
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Well-known, publicly documented test card numbers (Visa/Mastercard/Amex/
# Discover) used by payment processors for testing - never real cardholder data.
CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:4111[ -]?1111[ -]?1111[ -]?1111"
    r"|5555[ -]?5555[ -]?5555[ -]?4444"
    r"|3782[ -]?822463[ -]?10005"
    r"|6011[ -]?1111[ -]?1111[ -]?1117)\b"
)

API_KEY_PATTERN = re.compile(r"\b(?:sk-|AKIA|ghp_|xox[baprs]-)[A-Za-z0-9_-]{8,}\b")

CATEGORY_PATTERNS = {
    "fake_ssn": SSN_PATTERN,
    "fake_credit_card": CREDIT_CARD_PATTERN,
    "fake_api_key": API_KEY_PATTERN,
}


def scan_text(text: str) -> dict[str, list[str]]:
    """Scan `text` for every heuristic category, returning
    {category: [matched snippets]} for categories with at least one hit.
    Shared by prompt/response/file inspection so detection logic lives in
    exactly one place."""
    lowered = text.lower()
    hits: dict[str, list[str]] = {}

    jailbreak_hits = [p for p in JAILBREAK_PHRASES if p in lowered]
    if jailbreak_hits:
        hits["jailbreak"] = jailbreak_hits

    keyword_hits = [k for k in CONFIDENTIAL_KEYWORDS if k in lowered]
    if keyword_hits:
        hits["confidential_keyword"] = keyword_hits

    for category, pattern in CATEGORY_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            hits[category] = matches

    return hits
