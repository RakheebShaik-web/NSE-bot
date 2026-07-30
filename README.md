# Leader Score India — research edition

This is an India-specific, leakage-safe rebuild of Leader Score V2. It is not
a promise of predictive accuracy. Accuracy must be demonstrated on
point-in-time Indian data and untouched out-of-sample periods.

## What changed

- NIFTY 500 point-in-time universe instead of a current constituent list.
- NIFTY 50 market regime plus market breadth.
- 6- and 12-month momentum excluding the latest month, adjusted indirectly
  through an explicit low-volatility component.
- 3-month momentum, 20-day relative strength and relative volume are supporting
  factors; the original 3–10-day formula is not copied.
- Median traded-value liquidity filter in rupees.
- No unexplained 95–98 score dead zone and no automatic 2x leverage.
- Signal at T close, fill at T+1 open. This prevents close/3:20 lookahead.
- Gap-aware ATR trailing stops and explicit round-trip friction.

## Required data

One CSV:

```text
date,ticker,open,high,low,close,volume,sector,in_universe
2020-01-01,RELIANCE,....,Energy,True
2020-01-01,NIFTY50,....,INDEX,False
```

Use adjusted OHLC values, point-in-time `in_universe`, delisted securities,
and NSE trading dates. Do not use today's NIFTY 500 list for the entire past.

## Run

```powershell
python backtest.py --input path\to\india_panel.csv
```

Outputs are written to `output/backtest`.

### Yahoo Finance research data

For development and backtesting, install the dependencies and build a daily
adjusted NSE panel from Yahoo Finance:

```powershell
python -m pip install -r requirements.txt
python fetch_yahoo.py --universe midsmall400 --start 2018-01-01
python backtest.py --input data\yahoo_india_panel.csv
python compare_caps.py --start 2018-01-01
python optimize_strategy.py --input data\yahoo_midcap150_panel.csv
```

The default `midsmall400` universe downloads the current official NIFTY
MidSmallcap 400 constituents (NIFTY Midcap 150 plus NIFTY Smallcap 250).
`universe_nse.csv` remains available as a quick 20-stock smoke-test universe.
Replace the current constituent list with dated, point-in-time membership
before treating results as serious research.
Yahoo is not used for live execution, and the generated data must not be
redistributed. The downloader uses adjusted daily OHLC so splits and dividends
do not create false momentum or returns.

## Dashboard

The research dashboard source is in `dashboard/`. It includes the equity/P&L
curve, drawdown analysis, annual returns, trade ledger and factor diagnostics.
The figures currently embedded in the UI are explicitly marked as illustrative
until a point-in-time NSE dataset is connected.

```powershell
cd dashboard
pnpm install
pnpm exec vinext dev
```

## Research protocol

1. Freeze a family of economically justified factor variants.
2. Use expanding walk-forward folds with a 10-session purge and embargo.
3. Choose weights only inside each training fold.
4. Aggregate only untouched OOS results.
5. Compare against NIFTY 50 TRI and an equal-weight NIFTY 500 benchmark.
6. Reject the model if OOS Sharpe is below 1, max drawdown exceeds 25%, results
   depend on one year, or reasonable cost/slippage changes destroy the edge.
7. Paper trade at least 30 completed positions before risking capital.

Important disclosure: this is hypothetical research, not investment advice.
Backtests can be materially wrong because of survivorship bias, corporate
actions, taxes, costs, liquidity, price limits, gaps and execution assumptions.
