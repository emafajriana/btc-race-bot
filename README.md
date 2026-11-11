# BTC Race Bot

## Strategy: EMA/RSI-Gated Impulse

On each consecutive one-minute CBBTC close, buy when the close is at least 14 bps above the previous close, EMA(9) is above EMA(21), and Wilder RSI(14) is below 75. Spend 50% of available cash, subject to the 1 USDC minimum. Sell the full position after eight bars, counting from the entry decision bar. Orders use a 100 bps maximum-slippage guard and fill at the next bar's open. No bar-volume filter is used because volume is null in this dataset. Indicators reset after a timestamp gap, and no entry is made across a gap.

The harness first sends a hello with the CBBTC scales, caps, fees, seed, and initial 1,000 USDC. The bot then receives one batch per minute with the current bar, prior fills, and account state; its reply is decided from the close and fills at the following open.

## Development results

The frozen window has 1,440 bars, no missing minutes, a close-to-close return of about -107 bps, and 221 flat minutes. The median absolute one-minute move is about 1.97 bps. The original 35 bps impulse fired once, yielding only two fills and +$0.698630.

All six bundled baselines were graded with the local Node process driver:

| Baseline | Net PnL (USDC) | Max drawdown | Fills |
|---|---:|---:|---:|
| ADX momentum | -59.400241 | 6.240066% | 35 |
| Buy and hold | -13.442095 | 2.841636% | 1 |
| EMA crossover | -89.289844 | 9.221588% | 65 |
| Hold cash | 0.000000 | 0.000000% | 0 |
| Momentum | -12.033818 | 2.702840% | 1 |
| RSI-Bollinger | -29.651353 | 3.118025% | 16 |

The focused grid also tested lower-threshold impulse, rolling-mean reversion, Donchian breakout, filtered EMA, and the specified impulse/EMA/RSI, MACD momentum-confluence, and RSI/MACD oversold-reversal rules. The selected TypeScript mirror scored **+$1.354400 net PnL**, **0.141174% max drawdown**, and **6 fills** (three round trips); fees were $1.201115 and the doubled-fee net remained positive at $0.153535. This is above the dev gate but below the $5 search target.

## Neighbor plateau

The six immediate neighbors were threshold 13/15 bps, hold 7/9 bars, and 25/75% sizing: five were profitable, with the 7-bar hold the exception at -$3.008194. Two additional checks (16 bps and 100% sizing) were also profitable. Overall, 7 of 8 tested variants were positive, ranging from -$3.008194 to +$1.137258. This is a mostly profitable but small-margin plateau, not evidence that the strategy will generalize to the unseen race window.

## Python cross-check

A subprocess replay of `main.py` used the saved grade hello, all 1,440 development bars, next-open fills, and a simplified 6 bps friction model without pool impact. It produced **6 fills** and **+$2.558650** PnL, matching the TypeScript mirror's fill count and PnL sign; the PnL differs because the local driver omits the harness's pool-impact model.
