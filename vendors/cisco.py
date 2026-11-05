"""Live integration for Cisco AI Defense (Inspection API).

Calls POST {base_url}/api/v1/inspect/chat - see
https://developer.cisco.com/docs/ai-defense-inspection/inspect-conversations/
for the schema this is built against. Auth is an API key (generated from the
AI Defense UI) sent in the X-Cisco-AI-Defense-API-Key header. See
CISCO_AI_DEFENSE_API_KEY / CISCO_AI_DEFENSE_BASE_URL in config.py / .env.
Unlike the other vendors there is no mock to fall back to, so this appears in
the Live Vendor Test tab only when a key is set.

The published schema omits it, but the live API returns an "action" field
("Block"/"Allow"); that drives the verdict. Anything detected (rules or PII)
while the action is Allow becomes "flag". Severity is NONE_SEVERITY for most
detections, so it is not used.
"""

import requests

from vendors.base import Outcome, Verdict, VendorAPIError

INSPECT_PATH = "/api/v1/inspect/chat"
REQUEST_TIMEOUT_SECONDS = 20

ALL_RULES = [
    "Code Detection",
    "Harassment",
    "Hate Speech",
    "PCI",
    "PHI",
    "PII",
    "Prompt Injection",
    "Profanity",
    "Sexual Content & Exploitation",
    "Social Division & Polarization",
    "Violence & Public Safety Threats",
]


class CiscoAIDefenseProvider:
    name = "Cisco AI Defense"

    def __init__(self, api_key: str, base_url: str, rules: list[str] | None = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.rules = rules or ALL_RULES

    def _inspect(self, role: str, content: str) -> dict:
        payload = {
            "messages": [{"role": role, "content": content}],
            "metadata": {"user": "live-vendor-test", "src_app": "AIThreatNotebook"},
            "config": {"enabled_rules": [{"rule_name": r} for r in self.rules]},
        }
        try:
            resp = requests.post(
                f"{self.base_url}{INSPECT_PATH}",
                headers={
                    "X-Cisco-AI-Defense-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise VendorAPIError(f"{self.name}: request to {self.base_url} failed - {exc}") from exc

        if resp.status_code != 200:
            raise VendorAPIError(
                f"{self.name}: API returned HTTP {resp.status_code} - {resp.text[:500]}"
            )
        try:
            return resp.json()
        except ValueError as exc:
            raise VendorAPIError(f"{self.name}: API returned a non-JSON response - {exc}") from exc

    def _verdict_from_result(self, result: dict) -> Verdict:
        pii = sorted(
            {d.get("type", "").removeprefix("PII_ENTITY_TYPE_") for d in result.get("detected_pii") or []} - {""}
        )
        signals = sorted({r.get("rule_name", "unknown") for r in result.get("rules") or []}) + pii

        outcome: Outcome
        if str(result.get("action", "")).lower() == "block":
            outcome = "block"
        elif not result.get("is_safe", True) or signals:
            # Detected, but the API's action was Allow (e.g. PII it did not block).
            outcome = "flag"
        else:
            outcome = "allow"

        what = ", ".join(signals) or ", ".join(result.get("classifications") or []) or "violation"
        if outcome == "block":
            reason = f"{self.name}: {what} detected, request blocked."
        elif outcome == "flag":
            reason = f"{self.name}: {what} detected but not blocked, flagged for review."
        else:
            reason = f"{self.name}: no policy violations detected, request allowed."

        if result.get("event_id"):
            reason += f" [event {result['event_id']}]"
        return Verdict(vendor=self.name, outcome=outcome, reason=reason, signals=signals)

    def inspect_prompt(self, text: str) -> Verdict:
        return self._verdict_from_result(self._inspect("user", text))

    def inspect_response(self, text: str) -> Verdict:
        return self._verdict_from_result(self._inspect("assistant", text))

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
        return self._verdict_from_result(self._inspect("user", text))
