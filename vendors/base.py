from dataclasses import dataclass, field
from typing import Literal, Protocol

Outcome = Literal["allow", "flag", "block"]


@dataclass
class Verdict:
    vendor: str
    outcome: Outcome
    reason: str
    signals: list[str] = field(default_factory=list)


class SecurityProvider(Protocol):
    name: str

    def inspect_prompt(self, text: str) -> Verdict: ...

    def inspect_response(self, text: str) -> Verdict: ...

    def inspect_file(self, filename: str, content_bytes: bytes, content_type: str) -> Verdict: ...


class VendorAPIError(Exception):
    """Raised by a live (real HTTP-calling) provider when a vendor API call
    fails - network error, non-2xx response, or a malformed response body.
    Callers should surface this distinctly from a Verdict, since it means the
    vendor was never actually able to render a verdict."""
