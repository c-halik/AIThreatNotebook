"""Mock security-vendor providers.

These are NOT real integrations - none of the 8 vendors named here have an
API wired up yet. Each mock applies the same shared heuristics
(`vendors/heuristics.py`) with different strictness thresholds and reason
phrasing, so switching vendors on identical input gives visibly different
verdicts for comparison purposes. The block/flag thresholds and phrasing
below are illustrative guesses, not validated against real vendor behavior -
swap in a real HTTP-calling implementation per vendor as credentials become
available (see `vendors/registry.py`).
"""

from dataclasses import dataclass, field

from vendors.base import Outcome, Verdict
from vendors.heuristics import scan_text

ALL_CATEGORIES = frozenset(
    {"jailbreak", "confidential_keyword", "fake_ssn", "fake_credit_card", "fake_api_key"}
)


@dataclass
class VendorProfile:
    name: str
    block_categories: frozenset[str] = frozenset()
    flag_categories: frozenset[str] = ALL_CATEGORIES
    block_combos: list[frozenset[str]] = field(default_factory=list)
    block_min_distinct: int | None = None
    block_phrase: str = "policy violation"
    flag_phrase: str = "policy signal"


def _decide(categories_hit: set[str], profile: VendorProfile) -> tuple[Outcome, list[str]]:
    for combo in profile.block_combos:
        if combo <= categories_hit:
            return "block", sorted(combo)

    if profile.block_min_distinct and len(categories_hit) >= profile.block_min_distinct:
        return "block", sorted(categories_hit)

    block_hits = categories_hit & profile.block_categories
    if block_hits:
        return "block", sorted(block_hits)

    flag_hits = categories_hit & profile.flag_categories
    if flag_hits:
        return "flag", sorted(flag_hits)

    if categories_hit:
        return "flag", sorted(categories_hit)

    return "allow", []


class MockSecurityProvider:
    def __init__(self, profile: VendorProfile):
        self.profile = profile
        self.name = profile.name

    def _verdict_from_text(self, text: str) -> Verdict:
        categories_hit = scan_text(text)
        outcome, matched = _decide(set(categories_hit.keys()), self.profile)
        if outcome == "block":
            reason = f"{self.name}: {self.profile.block_phrase} — {', '.join(matched)} detected, request blocked."
        elif outcome == "flag":
            reason = f"{self.name}: {self.profile.flag_phrase} — {', '.join(matched)} detected, flagged for review."
        else:
            reason = f"{self.name}: no policy violations detected, request allowed."
        return Verdict(vendor=self.name, outcome=outcome, reason=reason, signals=matched)

    def inspect_prompt(self, text: str) -> Verdict:
        return self._verdict_from_text(text)

    def inspect_response(self, text: str) -> Verdict:
        return self._verdict_from_text(text)

    def inspect_file(self, filename: str, content_bytes: bytes, content_type: str) -> Verdict:
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return Verdict(
                vendor=self.name,
                outcome="flag",
                reason=f"{self.name}: unrecognized binary content in {filename} — unable to inspect payload, flagged for manual review.",
                signals=["undecodable_binary"],
            )
        return self._verdict_from_text(text)


VENDOR_PROFILES: list[VendorProfile] = [
    VendorProfile(
        name="Prisma AIRS",
        block_categories=frozenset({"jailbreak", "fake_ssn", "fake_credit_card", "fake_api_key"}),
        flag_categories=frozenset({"confidential_keyword"}),
        block_phrase="policy violation",
        flag_phrase="policy signal",
    ),
    VendorProfile(
        name="CrowdStrike AIDR",
        block_min_distinct=2,
        flag_categories=ALL_CATEGORIES,
        block_phrase="behavioral anomaly",
        flag_phrase="behavioral signal",
    ),
    VendorProfile(
        name="SentinelOne Prompt Security",
        block_categories=frozenset({"jailbreak"}),
        flag_categories=frozenset({"confidential_keyword", "fake_ssn", "fake_credit_card", "fake_api_key"}),
        block_phrase="prompt injection detected",
        flag_phrase="sensitive data signal",
    ),
    VendorProfile(
        name="Zscaler",
        block_combos=[
            frozenset({"confidential_keyword", "fake_ssn"}),
            frozenset({"confidential_keyword", "fake_credit_card"}),
            frozenset({"confidential_keyword", "fake_api_key"}),
        ],
        flag_categories=ALL_CATEGORIES,
        block_phrase="DLP policy violation",
        flag_phrase="DLP policy signal",
    ),
    VendorProfile(
        name="Netskope",
        block_combos=[
            frozenset({"fake_api_key", "jailbreak"}),
            frozenset({"fake_api_key", "fake_ssn"}),
            frozenset({"fake_api_key", "fake_credit_card"}),
            frozenset({"fake_api_key", "confidential_keyword"}),
        ],
        flag_categories=ALL_CATEGORIES,
        block_phrase="cloud DLP posture violation",
        flag_phrase="cloud DLP posture signal",
    ),
    VendorProfile(
        name="Saf3ai",
        block_categories=frozenset({"jailbreak", "fake_api_key"}),
        flag_categories=frozenset({"fake_ssn", "fake_credit_card", "confidential_keyword"}),
        block_phrase="secrets exposure",
        flag_phrase="potential secrets exposure",
    ),
    VendorProfile(
        name="LangGuard",
        block_categories=frozenset({"jailbreak"}),
        flag_categories=frozenset({"confidential_keyword", "fake_ssn", "fake_credit_card", "fake_api_key"}),
        block_phrase="prompt-injection signature match",
        flag_phrase="prompt-injection signature (low confidence)",
    ),
    VendorProfile(
        name="HiddenLayer",
        block_categories=frozenset({"jailbreak"}),
        flag_categories=frozenset({"fake_ssn", "fake_credit_card", "fake_api_key", "confidential_keyword"}),
        block_phrase="adversarial input detected",
        flag_phrase="adversarial input signal",
    ),
]
