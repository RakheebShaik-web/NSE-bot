# India adaptation research notes

## Decisions

1. **Universe:** NIFTY 500 is the broad research universe. Historical membership
   must be point-in-time. A present-day constituent file is unacceptable for a
   historical accuracy claim.
2. **Benchmark:** NIFTY 50 is used for relative strength and the market regime.
3. **Momentum horizon:** NSE Indices' own momentum methodology uses 6- and
   12-month returns adjusted for volatility. Those horizons therefore receive
   55% of this model's weight. Three-month and 20-session strength are secondary.
4. **Liquidity:** median 20-session traded value is used instead of share volume.
   This is comparable across securities with very different rupee prices.
5. **Timing:** default signals are calculated after the official 15:30 close and
   filled at the next regular session open. A 15:20 live variant is valid only
   when every feature, rank and benchmark value is rebuilt from intraday bars
   ending no later than 15:20.
6. **Risk:** no leverage by default. Indian equities have overnight gap, price
   band and circuit risks, so a stop price is not a guaranteed fill price.
7. **Costs:** the default 35 bps round trip is intentionally conservative but
   must be replaced with the user's broker-specific brokerage, STT, stamp duty,
   exchange charges, SEBI charges, GST, bid/ask spread and market impact.

## Features rejected from the original

- The 92–95 leveraged band and 95–98 dead zone: no India-specific economic
  justification and high data-mining risk.
- Full-day relative volume for a same-day pre-close entry: timing leakage.
- A current constituent universe applied backward: survivorship bias.
- Automatic 2x exposure: incompatible with the accuracy-first objective.

## Primary references

- NSE market timings: https://www.nseindia.com/static/market-data/market-timings
- NIFTY 500 overview/methodology:
  https://www.niftyindices.com/docs/default-source/indices/nifty-500/nifty-500-whitepaper_2024.pdf
- NIFTY200 Momentum 30 methodology:
  https://www.niftyindices.com/indices/equity/strategy-indices/nifty200-momentum-30
- NSE liquidity and stale-price discussion:
  https://www.niftyindices.com/resources/index-concepts/faqs
- NSE circuit breakers:
  https://www.nseindia.com/products-services/equity-market-circuit-breakers
- SEBI optional T+0 circular (existing cash market remains principally T+1):
  https://www.sebi.gov.in/legal/circulars/dec-2024/enhancement-in-the-scope-of-optional-t-0-rolling-settlement-cycle-in-addition-to-the-existing-t-1-rolling-settlement-cycle-in-equity-cash-markets_89443.html
