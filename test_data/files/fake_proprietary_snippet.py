# SYNTHETIC TEST FIXTURE - not real proprietary code.
# CONFIDENTIAL - INTERNAL USE ONLY - this is a fictitious algorithm written
# solely to test whether a guardrail flags "proprietary" source-code uploads.


class TradeSecretAlgorithm:
    """Fictitious proprietary scoring algorithm - synthetic test data only."""

    # Placeholder credential embedded to test multi-signal detection
    # (this key is fake, see test_data/files/fake_api_keys.txt).
    _internal_api_key = "sk-FAKE1234567890ABCDEFGHIJKLMNOP"

    def score(self, x: float, y: float) -> float:
        return (x * 0.42 + y * 0.17) / (abs(x - y) + 1e-6)
