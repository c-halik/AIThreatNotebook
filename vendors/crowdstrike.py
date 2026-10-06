"""Live integration for CrowdStrike AIDR (AI Detection and Response) AI Guard.

Calls POST {base_url}/v1/guard_chat_completions - see
https://aidr-docs.crowdstrike.com/docs/aidr/apis for the schema this is built
against. Auth is a Bearer token from an Application collector registered in
the Falcon console (AI detection and response > Collectors); the policy that
runs is bound to that collector, so requests carry no policy ID. See
CROWDSTRIKE_AIDR_TOKEN / CROWDSTRIKE_AIDR_BASE_URL in config.py / .env. Wired
in as the "CrowdStrike AIDR" entry in vendors/registry.py only when a token is
set - otherwise that entry stays the local heuristic mock.
"""

import requests

from vendors.base import Outcome, Verdict, VendorAPIError

SCAN_PATH = "/v1/guard_chat_completions"
REQUEST_TIMEOUT_SECONDS = 20


class CrowdStrikeAIDRProvider:
    name = "CrowdStrike AIDR"

    def __init__(self, token: str, base_url: str, app_id: str):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.app_id = app_id

    def _scan(self, content: str, event_type: str) -> dict:
        role = "user" if event_type == "input" else "assistant"
        payload = {
            "guard_input": {"messages": [{"role": role, "content": content}]},
            "event_type": event_type,
            "app_id": self.app_id,
            "user_id": "live-vendor-test",
        }
        try:
            resp = requests.post(
                f"{self.base_url}{SCAN_PATH}",
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
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

    def _verdict_from_scan(self, body: dict, event_type: str) -> Verdict:
        result = body.get("result") or {}
        detectors = result.get("detectors") or {}
        detected = sorted(name for name, d in detectors.items() if d.get("detected"))
        policy = result.get("policy", "unknown")

        outcome: Outcome
        if result.get("blocked"):
            outcome = "block"
        elif detected or result.get("transformed"):
            # A detector fired (or content was redacted) without a block.
            outcome = "flag"
        else:
            outcome = "allow"

        if outcome == "block":
            reason = f"{self.name}: policy '{policy}' blocked this request — {', '.join(detected) or 'policy'} detected."
        elif outcome == "flag":
            what = ", ".join(detected) or "content transformed"
            reason = f"{self.name}: policy '{policy}' detected {what} but did not block it - flagged for review."
        else:
            reason = f"{self.name}: policy '{policy}' found no policy violations, request allowed."

        reason += f" [event {event_type}]"
        return Verdict(vendor=self.name, outcome=outcome, reason=reason, signals=detected)

    def inspect_prompt(self, text: str) -> Verdict:
        return self._verdict_from_scan(self._scan(text, "input"), "input")

    def inspect_response(self, text: str) -> Verdict:
        return self._verdict_from_scan(self._scan(text, "output"), "output")

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
        return self._verdict_from_scan(self._scan(text, "input"), "input")
