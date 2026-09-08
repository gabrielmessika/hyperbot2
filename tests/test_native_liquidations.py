import runpy

compare = runpy.run_path("scripts/audit_native_liquidations.py")["compare"]


def sample() -> tuple[dict, dict]:
    archived = {
        "coin": "BTC",
        "timestamp": "1970-01-01T00:00:01Z",
        "trade_id": 1,
        "tx_hash": "hash",
        "side": "A",
        "direction": "Close Long",
        "liquidated_user": "owner",
        "price": "100",
        "size": "2",
        "mark_price": "101",
        "closed_pnl": "-3",
    }
    native = {
        "coin": "BTC",
        "time": 1000,
        "tid": 1,
        "hash": "hash",
        "side": "A",
        "dir": "Close Long",
        "px": "100.0",
        "sz": "2.000",
        "closedPnl": "-3.00",
        "liquidation": {
            "liquidatedUser": "owner",
            "markPx": "101.0",
            "method": "market",
        },
    }
    return archived, {
        "http_status": "200",
        "request": {"type": "userFillsByTime", "user": "owner"},
        "response": [native],
    }


def test_decimal_formatting_does_not_create_false_price_mismatch() -> None:
    archived, envelope = sample()
    result = compare(archived, envelope)
    assert result["verified"]
    assert not result["coverage_validated"]
    assert not result["liquidator_identity_validated"]


def test_matching_fill_without_liquidation_flag_is_not_forced_sale() -> None:
    archived, envelope = sample()
    del envelope["response"][0]["liquidation"]
    assert not compare(archived, envelope)["verified"]
    archived, envelope = sample()
    envelope["response"][0]["liquidation"]["liquidatedUser"] = "counterparty"
    assert not compare(archived, envelope)["verified"]


def test_price_mismatch_and_duplicate_trade_cannot_pass() -> None:
    archived, envelope = sample()
    envelope["response"][0]["px"] = "99"
    assert not compare(archived, envelope)["verified"]
    archived, envelope = sample()
    envelope["response"].append(envelope["response"][0])
    assert not compare(archived, envelope)["verified"]
