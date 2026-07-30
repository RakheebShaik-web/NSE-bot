# Capitalisation universe comparison

Same strategy configuration, Yahoo-adjusted daily candles, current official
NSE constituents, 2018-01-01 through 2026-07-29. No parameters were changed
between universes. Results include 35 bps round-trip friction.

| Universe | Trades | Total return | CAGR | Max drawdown | Win rate | Sharpe | Profit factor |
|---|---:|---:|---:|---:|---:|---:|---:|
| NIFTY Midcap 150 | 666 | +84.45% | +9.27% | -34.76% | 45.50% | 0.66 | 1.22 |
| NIFTY 50 | 268 | +13.33% | +1.82% | -48.46% | 49.63% | 0.23 | 1.14 |
| NIFTY 100 | 438 | +0.80% | +0.11% | -54.05% | 43.84% | 0.15 | 1.11 |
| NIFTY 500 | 1,091 | -12.97% | -2.02% | -40.00% | 41.06% | -0.01 | 1.00 |
| NIFTY MidSmallcap 400 | 994 | -21.05% | -3.43% | -42.87% | 40.74% | -0.11 | 0.97 |
| NIFTY Smallcap 250 | 673 | -34.25% | -6.01% | -58.29% | 37.30% | -0.19 | 0.81 |

## Interpretation

Midcap 150 is the only segment with a meaningful positive result under the
unchanged rules. It is now the research dashboard feed. Its 34.76% maximum
drawdown and sub-1 Sharpe remain below the project acceptance criteria, so it
is not approved for live or paper execution without walk-forward validation.

## Bias warning

These runs use today's constituent lists through history. That creates
survivorship bias. The comparison is useful as a cap-segment diagnostic, not
as a final estimate of deployable performance.
