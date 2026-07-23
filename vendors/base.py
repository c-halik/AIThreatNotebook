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
