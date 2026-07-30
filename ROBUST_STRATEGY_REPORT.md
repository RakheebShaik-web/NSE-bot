# Robust strategy research report

## Objective

Improve the NIFTY Midcap 150 strategy toward a 20–35% annual return while
requiring maximum drawdown below 25%, Sharpe above 1.2, realistic costs, and
positive expanding walk-forward performance.

## Research design

- Yahoo-adjusted daily candles, 2018-01-01 through 2026-07-29.
- Current NIFTY Midcap 150 constituents; survivorship bias remains.
- Signal formed at close and executed at next-session open.
- 35 bps round-trip cost.
- 72 bounded candidates:
  - 10- and 20-session holding periods.
  - 2.5x and 3.5x ATR trailing exits.
  - Score thresholds 80, 85 and 90.
  - Market breadth minimums 45% and 55%.
  - Balanced, faster and steadier momentum weight families.
- Five expanding folds with a two-week embargo.
- Candidate selection penalised drawdowns and rejected sparse trials.

## Best full-history candidate

`h10_atr3.5_s80_b0.55_balanced`

| Metric | Result |
|---|---:|
| Total return | +150.97% |
| Approximate CAGR | +13.2% |
| Maximum drawdown | -34.17% |
| Sharpe | 0.93 |
| Trades | 467 |

## Walk-forward result

The parameters selected independently in each expanding training fold produced:

| Metric | Result |
|---|---:|
| Stitched OOS return | +4.49% |
| Maximum drawdown | -43.68% |
| Sharpe | 0.27 |
| Return observations | 53 |
| Candidates tested | 72 |

## Cost sensitivity of the full-history candidate

| Round-trip cost | Total return | Max drawdown | Sharpe |
|---:|---:|---:|---:|
| 35 bps | +150.97% | -34.17% | 0.93 |
| 70 bps | +76.60% | -39.37% | 0.63 |
| 100 bps | +30.54% | -43.51% | 0.37 |

The edge degrades sharply as costs increase, which reinforces the rejection.

## Decision

Rejected. The full-history result is materially better than the baseline, but
the improvement does not survive untouched walk-forward evaluation. No
candidate is promoted to the dashboard or approved for paper/live execution.

Further progress requires point-in-time constituents and a different source of
alpha—not a wider parameter search over the same momentum formulation.
