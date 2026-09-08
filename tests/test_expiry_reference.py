from copy import deepcopy
from decimal import Decimal

from hyperbot2.research.expiry_reference import okx_usdt_midpoint


def reference() -> dict:
    return {
        "logged_ms": 100_000,
        "reference_sources": [
            {
                "source": "okx",
                "raw": {
                    "instId": "BTC-USDT",
                    "instType": "SPOT",
                    "ts": "99000",
                    "bidPx": "100",
                    "askPx": "102",
                },
            }
        ],
    }


def test_reference_requires_quote_currency_and_available_timestamp() -> None:
    record = reference()
    assert okx_usdt_midpoint(record, underlying="BTC", decision_ms=110_000) == Decimal(
        101
    )
    for changes in (
        {"instId": "BTC-USD"},
        {"instType": "SWAP"},
        {"ts": "100001"},  # Exchange data cannot postdate logged availability.
        {"ts": "49999"},
        {"bidPx": "103"},
        {"askPx": "NaN"},
    ):
        bad = deepcopy(record)
        bad["reference_sources"][0]["raw"].update(changes)
        assert okx_usdt_midpoint(bad, underlying="BTC", decision_ms=110_000) is None
    assert okx_usdt_midpoint(record, underlying="HYPE", decision_ms=110_000) is None
    assert okx_usdt_midpoint(record, underlying="BTC", decision_ms=99_000) is None
