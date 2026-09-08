import json
import runpy
from pathlib import Path

MODULE = runpy.run_path(
    str(Path(__file__).parents[1] / "scripts/extract_microstructure.py")
)


class Rows:
    def __init__(self) -> None:
        self.rows: list[tuple[object, ...]] = []

    def writerow(self, row: tuple[object, ...]) -> None:
        self.rows.append(row)


def payload(
    channel: str, event: int, received: int, **data: object
) -> dict[str, object]:
    return {
        "coin": "BTC",
        "channel": channel,
        "exchange_ts_ms": event,
        "receive_ts_ms": received,
        "context": {"run_id": "test"},
        "payload_json": json.dumps({"coin": "BTC", "time": event, **data}),
    }


def test_second_does_not_use_event_received_at_that_second() -> None:
    output = Rows()
    reducer = MODULE["Reducer"](output)

    def levels(px: int) -> list[dict[str, str]]:
        return [{"px": str(px), "sz": "100"}, {"px": str(px + 1), "sz": "100"}]

    reducer.observe(payload("bbo", 900, 1000, bbo=levels(100)))
    reducer.observe(payload("bbo", 1900, 2000, bbo=levels(200)))
    first = dict(zip(MODULE["COLUMNS"], output.rows[0], strict=True))
    assert first["time"] == 2000 and first["bid"] == 100
    reducer.observe(payload("bbo", 2900, 3000, bbo=levels(300)))
    second = dict(zip(MODULE["COLUMNS"], output.rows[1], strict=True))
    assert second["bid"] == 200


def test_trade_id_is_scoped_by_coin_and_block_time() -> None:
    reducer = MODULE["Reducer"](Rows())
    trade = dict(px="100", sz="1", side="B", tid=42)
    reducer.observe(payload("trades", 900, 1000, **trade))
    reducer.observe(payload("trades", 900, 1100, **trade))
    reducer.observe(payload("trades", 1200, 1300, **trade))
    assert reducer.counts["duplicate_trade"] == 1
    assert reducer.total["BTC"] == 200
    reducer.observe(payload("trades", 100, 2500, **trade))
    assert reducer.counts["event_late_or_future"] == 1
    assert reducer.total["BTC"] == 200
