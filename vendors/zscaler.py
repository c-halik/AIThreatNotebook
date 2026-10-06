"""Live integration for Zscaler AI Guard, Detection-as-a-Service (DAS/API)
mode - see
https://help.zscaler.com/secure-ai-apps-infra/quick-start-guide-dasapi-mode
for the request/response schema this is built against. Requires an API key
(created under AI Guard > AI Applications > Add API Keys) and a numeric
policy ID (from AI Guard > Policy > Configurations) - see
ZSCALER_AI_GUARD_API_KEY / ZSCALER_AI_GUARD_POLICY_ID in config.py / .env.
Wired in as the "Zscaler" entry in vendors/registry.py only when both are
set - otherwise that entry stays the local heuristic mock.

Per Zscaler's docs, DAS mode is advisory only ("AI Guard can only make
recommendations to the application, but it cannot perform enforcement
actions") - the caller (this app) is what has to honor the returned action.
"""

import requests

from vendors.base import Outcome, Verdict, VendorAPIError

SCAN_PATH = "/v1/detection/execute-policy"
REQUEST_TIMEOUT_SECONDS = 20


class ZscalerAIGuardProvider:
    name = "Zscaler"

    def __init__(self, api_key: str, policy_id: str, base_url: str):
        self.api_key = api_key
        self.policy_id = policy_id
        self.base_url = base_url.rstrip("/")

    def _scan(self, content: str, direction: str) -> dict:
        try:
            policy_id_value: int | str = int(self.policy_id)
        except (TypeError, ValueError):
            policy_id_value = self.policy_id

        payload = {"direction": direction, "policyId": policy_id_value, "content": content}
        try:
            resp = requests.post(
                f"{self.base_url}{SCAN_PATH}",
                headers={"Authorization": f"Bearer {self.api_key}"},
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

    def _verdict_from_scan(self, result: dict) -> Verdict:
        action = result.get("action", "ALLOW")
        detectors = result.get("detectorResponses") or {}
        triggered = sorted(name for name, d in detectors.items() if d.get("triggered"))

        outcome: Outcome
        if action == "BLOCK":
            outcome = "block"
        elif triggered:
            # A detector fired but the policy didn't map it to a block action.
            outcome = "flag"
        else:
            outcome = "allow"

        if outcome == "block":
            reason = (
                f"{self.name}: policy {self.policy_id} blocked this request — "
                f"{', '.join(triggered) or 'detector'} triggered."
            )
        elif outcome == "flag":
            reason = (
                f"{self.name}: policy {self.policy_id} detected {', '.join(triggered)} "
                "but did not block it - flagged for review."
            )
        else:
            reason = f"{self.name}: policy {self.policy_id} found no policy violations, request allowed."

        reason += f" [direction {result.get('direction')}, transaction {result.get('transactionId')}]"
        return Verdict(vendor=self.name, outcome=outcome, reason=reason, signals=triggered)

    def inspect_prompt(self, text: str) -> Verdict:
        result = self._scan(text, direction="IN")
        return self._verdict_from_scan(result)

    def inspect_response(self, text: str) -> Verdict:
        result = self._scan(text, direction="OUT")
        return self._verdict_from_scan(result)

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
        result = self._scan(text, direction="IN")
        return self._verdict_from_scan(result)
