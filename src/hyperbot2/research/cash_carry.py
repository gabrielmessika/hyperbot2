"""Static spot/perpetual hedge economics with separate venue collateral."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_FLOOR, Decimal

from hyperbot2.research.volume import VolumeBar

D = Decimal
HOUR = 3600000
BASE_FEE_HL = D("0.00045")
BASE_FEE_SPOT = D("0.003")
BASE_SLIP_HL = D("0.0002")
BASE_SLIP_SPOT = D("0.0005")
BASE_FX_COST = D("0.001")
ONE = D(1)


def carry_period(
    hl: Mapping[int, VolumeBar],
    spot: Mapping[int, VolumeBar],
    fx: Mapping[int, VolumeBar],
    funding: Mapping[int, Decimal],
    start: int,
    end: int,
    *,
    fee_hl: Decimal = BASE_FEE_HL,
    fee_spot: Decimal = BASE_FEE_SPOT,
    slip_hl: Decimal = BASE_SLIP_HL,
    slip_spot: Decimal = BASE_SLIP_SPOT,
    fx_cost: Decimal = BASE_FX_COST,
    funding_haircut: Decimal = ONE,
    lot: Decimal = ONE,
) -> dict[str, Decimal | str | int | None]:
    """1,000 USDC split equally across venues, with no collateral transfers.

    A 20% maintenance buffer is an explicit stress, not exchange liquidation math.
    No planned-exit PnL is returned if the intrahour high breaches this buffer.
    """
    if end <= start or start % HOUR or end % HOUR or lot <= 0:
        raise ValueError("invalid interval/lot")
    if not all(0 <= x < 1 for x in (fee_hl, fee_spot, slip_hl, slip_spot, fx_cost)):
        raise ValueError("invalid costs")
    if not 0 <= funding_haircut <= 1:
        raise ValueError("invalid funding haircut")
    required = set(range(start, end + HOUR, HOUR))
    if not all(required <= source.keys() for source in (hl, spot, fx)):
        raise ValueError("hedge candle coverage gap")
    if not (required - {start}) <= funding.keys():
        raise ValueError("funding coverage gap")
    if any(not funding[t].is_finite() for t in required - {start}):
        raise ValueError("non-finite funding")
    h_in, s_in = hl[start].open * (1 - slip_hl), spot[start].open * (1 + slip_spot)
    usdt = 500 * (1 - fx_cost) * fx[start].open
    quantity = (
        min(D(500) / h_in, usdt / (s_in * (1 + fee_spot))) / lot
    ).to_integral_value(rounding=ROUND_FLOOR) * lot
    if quantity <= 0:
        raise ValueError("position below lot size")
    leftover = usdt - quantity * s_in * (1 + fee_spot)
    h_entry_fee = quantity * h_in * fee_hl
    margin_cash = D(500) - h_entry_fee
    paid = D(0)
    min_buffer = D("Infinity")
    min_equity = D("Infinity")
    max_basis = D(0)
    for at in range(start, end + HOUR, HOUR):
        if at > start:
            rate = funding[at]
            receipt = (
                quantity * hl[at].open * rate * (funding_haircut if rate > 0 else 1)
            )
            paid += receipt
            margin_cash += receipt
        mark = hl[at].high if at < end else hl[at].open
        equity = margin_cash + quantity * (h_in - mark)
        buffer = equity - D("0.2") * quantity * mark
        min_equity, min_buffer = min(min_equity, equity), min(min_buffer, buffer)
        max_basis = max(
            max_basis, abs(hl[at].open / (spot[at].open / fx[at].open) - 1) * 10000
        )
        if buffer <= 0:
            return {
                "status": "MARGIN_STRESS_BREACH",
                "quantity": quantity,
                "first_breach_ms": at,
                "margin_equity_at_adverse_price": equity,
                "minimum_margin_buffer_usdc": min_buffer,
                "funding_received_to_breach": paid,
                "planned_exit_net_usdc": None,
                "max_open_basis_bps_to_breach": max_basis,
            }
    h_out, s_out = hl[end].open * (1 + slip_hl), spot[end].open * (1 - slip_spot)
    h_pnl = quantity * (h_in - h_out)
    h_exit_fee = quantity * h_out * fee_hl
    hl_final = margin_cash + h_pnl - h_exit_fee
    final_spot_usdt = leftover + quantity * s_out * (1 - fee_spot)
    spot_final = final_spot_usdt / fx[end].open * (1 - fx_cost)
    net = hl_final + spot_final - 1000
    return {
        "status": "COMPLETED_RESEARCH_HEDGE",
        "quantity": quantity,
        "planned_exit_net_usdc": net,
        "final_hl_cash_usdc": hl_final,
        "final_spot_proceeds_usdc": spot_final,
        "short_price_pnl_usdc": h_pnl,
        "funding_received_usdc": paid,
        "hl_fees_usdc": h_entry_fee + h_exit_fee,
        "minimum_margin_buffer_usdc": min_buffer,
        "minimum_margin_equity_usdc": min_equity,
        "max_open_basis_bps": max_basis,
        "net_after_20_usd_per_30d_budget": net
        - D(20) * D(end - start) / D(30 * 24 * HOUR),
    }
