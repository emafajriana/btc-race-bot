import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars


SYMBOL = "CBBTC"
IMPULSE_BPS = 35
HOLD_BARS = 5
BUY_FRACTION_BPS = 5000
MAX_SLIPPAGE_BPS = 100

previous_close = None
previous_t = None
entry_seq = None
pending_entry_seq = None


def on_batch(state, batch):
    global previous_close, previous_t, entry_seq, pending_entry_seq

    bar = next((item for item in batch["bars"] if item["symbol"] == SYMBOL), None)
    if bar is None:
        return []

    close = int(bar["c"])
    elapsed_one_minute = previous_t is not None and bar["t"] - previous_t == 60_000
    prior_close = previous_close
    previous_close = close
    previous_t = bar["t"]

    position = state.positions.get(SYMBOL)
    if position is not None:
        if entry_seq is None:
            entry_seq = pending_entry_seq if pending_entry_seq is not None else batch["seq"] - 1
        pending_entry_seq = None
        if batch["seq"] - entry_seq >= HOLD_BARS:
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": position.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    entry_seq = None
    pending_entry_seq = None
    if prior_close is None or not elapsed_one_minute:
        return []

    if close * 10_000 < prior_close * (10_000 + IMPULSE_BPS):
        return []

    amount = state.cash * BUY_FRACTION_BPS // 10_000
    if amount < int(state.hello["fees"]["min_notional_quote_units"]):
        return []

    pending_entry_seq = batch["seq"]
    return [{
        "side": "buy",
        "symbol": SYMBOL,
        "notional_quote_units": amount,
        "max_slippage_bps": MAX_SLIPPAGE_BPS,
    }]


makefun_bars.run(on_batch)
