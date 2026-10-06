"""Live integration for Palo Alto Networks Prisma AIRS (AI Runtime Security).

Calls the real synchronous Scan API - see
https://pan.dev/prisma-airs/api/airuntimesecurity/airuntimesecurityapi/ and
https://pan.dev/prisma-airs/api/airuntimesecurity/usecases/ for the request/
response schema this is built against. Requires an API key and a security
profile created in Strata Cloud Manager (PRISMA_AIRS_API_KEY /
PRISMA_AIRS_PROFILE_NAME in config.py / .env). Wired in as the "Prisma AIRS"
entry in vendors/registry.py only when both are set - otherwise that entry
stays the local heuristic mock.
"""

import uuid

import requests

from vendors.base import Outcome, Verdict, VendorAPIError

SCAN_PATH = "/v1/scan/sync/request"
REQUEST_TIMEOUT_SECONDS = 20


class PrismaAirsProvider:
    name = "Prisma AIRS"

    def __init__(self, api_key: str, profile_name: str, base_url: str, app_name: str):
        self.api_key = api_key
        self.profile_name = profile_name
        self.base_url = base_url.rstrip("/")
        self.app_name = app_name

    def _scan(self, content: dict) -> dict:
        payload = {
            "tr_id": str(uuid.uuid4()),
            "ai_profile": {"profile_name": self.profile_name},
            "metadata": {"app_name": self.app_name, "app_user": "live-vendor-test"},
            "contents": [content],
        }
        try:
            resp = requests.post(
                f"{self.base_url}{SCAN_PATH}",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "x-pan-token": self.api_key,
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

    def _verdict_from_scan(self, result: dict, detected_key: str) -> Verdict:
        action = result.get("action", "allow")
        category = result.get("category", "benign")
        detected = result.get(detected_key) or {}
        signals = sorted(k for k, v in detected.items() if v is True)
        profile_name = result.get("profile_name", self.profile_name)

        outcome: Outcome
        if action == "block":
            outcome = "block"
        elif category == "malicious" or signals:
            # Profile is set to detect/alert rather than block this signal.
            outcome = "flag"
        else:
            outcome = "allow"

        if outcome == "block":
            reason = (
                f"{self.name}: profile '{profile_name}' blocked this request — "
                f"{', '.join(signals) or category} detected."
            )
        elif outcome == "flag":
            reason = (
                f"{self.name}: profile '{profile_name}' detected {', '.join(signals) or category} "
                "but did not block it - flagged for review."
            )
        else:
            reason = f"{self.name}: profile '{profile_name}' found no policy violations, request allowed."

        return Verdict(vendor=self.name, outcome=outcome, reason=reason, signals=signals)

    def inspect_prompt(self, text: str) -> Verdict:
        result = self._scan({"prompt": text})
        return self._verdict_from_scan(result, "prompt_detected")

    def inspect_response(self, text: str) -> Verdict:
        result = self._scan({"response": text})
        return self._verdict_from_scan(result, "response_detected")

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
        result = self._scan({"prompt": text})
        return self._verdict_from_scan(result, "prompt_detected")
