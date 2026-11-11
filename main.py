import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars


SYMBOL = "CBBTC"
IMPULSE_BPS = 14
HOLD_BARS = 8
BUY_FRACTION_BPS = 5000
MAX_SLIPPAGE_BPS = 100
EMA_FAST = 9
EMA_SLOW = 21
RSI_PERIOD = 14
RSI_MAX = 75

bars = []
previous_close = None
previous_t = None
pending_entry_seq = None
entry_seq = None


def ema(values, period):
    alpha = 2.0 / (period + 1)
    result = []
    for value in values:
        result.append(value if not result else result[-1] + alpha * (value - result[-1]))
    return result


def indicators():
    closes = [float(bar["c"]) for bar in bars]
    fast = ema(closes, EMA_FAST)
    slow = ema(closes, EMA_SLOW)
    rsi = [None] * len(closes)

    if len(closes) > RSI_PERIOD:
        gain = 0.0
        loss = 0.0
        for index in range(1, RSI_PERIOD + 1):
            change = closes[index] - closes[index - 1]
            if change > 0:
                gain += change
            else:
                loss -= change
        gain /= RSI_PERIOD
        loss /= RSI_PERIOD
        moved = gain + loss
        rsi[RSI_PERIOD] = 50.0 if moved == 0 else 100.0 * gain / moved

        for index in range(RSI_PERIOD + 1, len(closes)):
            change = closes[index] - closes[index - 1]
            gain = (gain * (RSI_PERIOD - 1) + max(change, 0.0)) / RSI_PERIOD
            loss = (loss * (RSI_PERIOD - 1) + max(-change, 0.0)) / RSI_PERIOD
            moved = gain + loss
            rsi[index] = 50.0 if moved == 0 else 100.0 * gain / moved

    return fast, slow, rsi


def on_batch(state, batch):
    global bars, previous_close, previous_t, pending_entry_seq, entry_seq

    bar = next((item for item in batch["bars"] if item["symbol"] == SYMBOL), None)
    if bar is None:
        return []

    close = int(bar["c"])
    elapsed_one_minute = previous_t is not None and bar["t"] - previous_t == 60_000
    prior_close = previous_close
    previous_close = close
    previous_t = bar["t"]
    bars.append(bar)
    if not elapsed_one_minute and len(bars) > 1:
        bars = [bar]

    fast, slow, rsi = indicators()
    index = len(bars) - 1
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

    current_rsi = rsi[index]
    impulse = close * 10_000 >= prior_close * (10_000 + IMPULSE_BPS)
    trend = fast[index] > slow[index]
    if not (impulse and trend and current_rsi is not None and current_rsi < RSI_MAX):
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
