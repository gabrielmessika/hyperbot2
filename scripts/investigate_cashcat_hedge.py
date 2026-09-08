"""Offline fixed-quantity hedge and separate-collateral diagnostic."""

from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.cash_carry import HOUR, carry_period
from hyperbot2.research.volume import VolumeBar

D = Decimal
DAY, START, SPLIT, END = 86400000, 1784160000000, 1786060800000, 1788652800000


def put(rows: dict, key: int, value: object) -> None:
    if key in rows and rows[key] != value:
        raise ValueError("conflicting overlapping archive rows")
    rows[key] = value


def inputs() -> tuple[dict, dict, dict, dict, dict, dict]:
    root = Path("data/wide_funding_2026-09-07")
    sources, hl, spot, fx, funding, metadata = {}, {}, {}, {}, {}, {}
    for folder in (
        root / "cashcat_hedge",
        root / "cashcat_boundaries",
        root / "history",
    ):
        manifest = folder / "manifest.json"
        sources[str(manifest)] = checked_input(manifest)
        m = json.loads(manifest.read_text())
        records = (
            m.get("external_requests", [])
            + m.get("native_requests", [])
            + m.get("requests", [])
        )
        for record in records:
            path = Path(record["path"])
            sources[str(path)] = checked_input(path)
            if sources[str(path)] != record["sha256"]:
                raise ValueError("manifest hash mismatch")
            raw = json.loads(path.read_text())
            if raw["returncode"]:
                raise ValueError("failed archive request")
            data = raw["response"]
            if "request" in raw:
                q = raw["request"]
                if q["type"] == "candleSnapshot":
                    for b in data:
                        if (
                            b["s"] != "CASHCAT"
                            or b["i"] != "1h"
                            or b["T"] != b["t"] + HOUR - 1
                        ):
                            raise ValueError("native candle identity mismatch")
                        put(
                            hl,
                            b["t"],
                            VolumeBar(
                                b["t"], *(D(b[k]) for k in ("o", "h", "l", "c", "v"))
                            ),
                        )
                elif q["type"] == "fundingHistory" and q["coin"] == "CASHCAT":
                    for f in data:
                        if (
                            f["coin"] != "CASHCAT"
                            or not D(f["fundingRate"]).is_finite()
                        ):
                            raise ValueError("invalid CASHCAT funding")
                        put(funding, int(f["time"]) // HOUR * HOUR, D(f["fundingRate"]))
            elif path.stem.startswith("fx_klines"):
                if "symbol=USDCUSDT" not in raw["url"]:
                    raise ValueError("unexpected FX pair")
                for b in data:
                    if b[6] != b[0] + HOUR - 1:
                        raise ValueError("invalid FX interval")
                    put(fx, b[0], VolumeBar(b[0], *(D(v) for v in b[1:6])))
            else:
                if data["code"] != "200000":
                    raise ValueError("KuCoin response error")
                value = data["data"]
                if path.stem == "spot_klines":
                    if (
                        value["symbol"] != "CASHCAT-USDT"
                        or value["tradeType"] != "SPOT"
                    ):
                        raise ValueError("incorrect hedge symbol/type")
                    for b in value["list"]:
                        at = int(b[0]) * 1000
                        if at % HOUR:
                            raise ValueError("invalid spot interval")
                        put(spot, at, VolumeBar(at, *(D(v) for v in b[1:6])))
                else:
                    metadata[path.stem] = value
    expected = set(range(START, END + DAY + HOUR, HOUR))
    if any(not expected <= rows.keys() for rows in (hl, spot, fx, funding)):
        raise ValueError("incomplete hourly hedge coverage")
    symbol = metadata["spot_symbol"]
    if (
        symbol["baseCurrency"] != "CASHCAT"
        or symbol["quoteCurrency"] != "USDT"
        or not symbol["enableTrading"]
        or D(symbol["baseIncrement"]) != D("0.01")
    ):
        raise ValueError("hedge metadata mismatch")
    address = metadata["spot_currency"]["chains"][0]["contractAddress"]
    if re.fullmatch("0x[0-9a-fA-F]{40}", address) is None:
        raise ValueError("invalid spot contract address")
    native = root / "meta.json"
    sources[str(native)] = checked_input(native)
    universe, _ = json.loads(native.read_text())["response"]
    coin = next(r for r in universe["universe"] if r["name"] == "CASHCAT")
    if coin["szDecimals"] != 0 or coin["maxLeverage"] != 3:
        raise ValueError("native lot/margin metadata changed")
    metadata["native"] = coin
    return hl, spot, fx, funding, sources, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/wide_funding_2026-09-07/CASHCAT_PROTOCOL.md")
    checked_input(protocol.parent / "cashcat_registration.json")
    if json.loads((protocol.parent / "cashcat_registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("hedge protocol changed")
    hl, spot, fx, funding, sources, metadata = inputs()
    scenarios = {
        "base": {},
        "cost_stress": {
            "fee_hl": D("0.0009"),
            "fee_spot": D("0.006"),
            "slip_hl": D("0.0005"),
            "slip_spot": D("0.001"),
            "fx_cost": D("0.002"),
        },
        "funding_half": {"funding_haircut": D("0.5")},
        "delay_day": {},
        "zero_cost_control": {
            "fee_hl": D(0),
            "fee_spot": D(0),
            "slip_hl": D(0),
            "slip_spot": D(0),
            "fx_cost": D(0),
        },
    }
    results = {}
    for name, (begin, finish) in {
        "older": (START, SPLIT),
        "selected_month": (SPLIT, END),
    }.items():
        results[name] = {
            s: carry_period(
                hl,
                spot,
                fx,
                funding,
                begin + (DAY if s == "delay_day" else 0),
                finish + (DAY if s == "delay_day" else 0),
                **kw,
            )
            for s, kw in scenarios.items()
        }
    valid = all(
        v["status"] == "COMPLETED_RESEARCH_HEDGE"
        and v["net_after_20_usd_per_30d_budget"] > 0
        for r in results.values()
        for s, v in r.items()
        if s != "zero_cost_control"
    )
    write_json(
        args.output / "summary.json",
        {
            "run_id": "cashcat-hedge-2026-09-07",
            "segments": results,
            "source_hashes": sources,
            "metadata": metadata,
            "start_ms": START,
            "split_ms": SPLIT,
            "end_ms": END,
            "protocol_sha256": file_sha256(protocol),
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("src/hyperbot2/research/cash_carry.py"),
                    Path("src/hyperbot2/research/volume.py"),
                )
            },
            "decision": "FURTHER_QUALIFICATION_REQUIRED"
            if valid
            else "HEDGE_ECONOMICS_NOT_CONFIRMED",
            "promotion_authorized": False,
            "data_cost_usd": 0,
            "limits": [
                "selected on latest-month funding; no independent portfolio holdout",
                "20% maintenance stress, not exact historical liquidation formula",
                "hourly traded prices, no executable quotes or exact funding oracle",
                "no transfers; no profit credited beyond margin stress breach",
                "fees and conversion costs assumed; network withdrawals unqualified",
                "spot contract checked, HL underlying mapping unqualified",
                "no prospective funding persistence or live authorization",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
