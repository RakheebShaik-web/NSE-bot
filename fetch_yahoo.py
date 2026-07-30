"""Download Yahoo Finance daily candles into the NSE-bot panel format.

Yahoo data is suitable for research/backtesting here, not order execution.
Using a current ticker list for past dates introduces survivorship bias; pass a
point-in-time universe file when evaluating production-quality results.
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
import yfinance as yf

PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
MIDSMALL400_URL = (
    "https://www.niftyindices.com/IndexConstituent/"
    "ind_niftymidsmallcap400list.csv"
)


def yahoo_symbol(ticker: str) -> str:
    ticker = ticker.upper().strip()
    if ticker.startswith("^") or ticker.endswith((".NS", ".BO")):
        return ticker
    return f"{ticker}.NS"


def normalize_symbol_frame(
    raw: pd.DataFrame,
    yahoo_ticker: str,
    output_ticker: str,
    sector: str,
    in_universe: bool,
) -> pd.DataFrame:
    """Convert one Yahoo symbol frame to the canonical strategy panel."""
    if raw.empty:
        return pd.DataFrame()
    frame = raw.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        if yahoo_ticker in frame.columns.get_level_values(-1):
            frame = frame.xs(yahoo_ticker, axis=1, level=-1)
        elif yahoo_ticker in frame.columns.get_level_values(0):
            frame = frame.xs(yahoo_ticker, axis=1, level=0)
    missing = set(PRICE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"{yahoo_ticker}: missing Yahoo columns {sorted(missing)}")
    frame = frame[PRICE_COLUMNS].rename(columns=str.lower)
    dates = pd.to_datetime(frame.index)
    if dates.tz is not None:
        dates = dates.tz_convert("Asia/Kolkata").tz_localize(None)
    frame["date"] = dates.normalize()
    frame["ticker"] = output_ticker
    frame["sector"] = sector or "UNKNOWN"
    frame["in_universe"] = bool(in_universe)
    frame = frame.reset_index(drop=True)
    numeric = ["open", "high", "low", "close", "volume"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=numeric)
    valid = (
        (frame["high"] >= frame[["open", "close", "low"]].max(axis=1))
        & (frame["low"] <= frame[["open", "close", "high"]].min(axis=1))
        & (frame[numeric] >= 0).all(axis=1)
    )
    return frame.loc[valid, ["date", "ticker", *numeric, "sector", "in_universe"]]


def load_universe(path: str | Path) -> pd.DataFrame:
    if str(path).lower() in {"midsmall400", "nifty-midsmallcap-400"}:
        request = Request(MIDSMALL400_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=30) as response:
            universe = pd.read_csv(io.BytesIO(response.read()))
        universe = universe.rename(
            columns={"Symbol": "ticker", "Industry": "sector"}
        )
    else:
        universe = pd.read_csv(path)
    if "ticker" not in universe:
        raise ValueError("Universe CSV must contain a ticker column")
    if "sector" not in universe:
        universe["sector"] = "UNKNOWN"
    universe["ticker"] = universe["ticker"].astype(str).str.upper().str.strip()
    return universe.drop_duplicates("ticker")


def download_panel(
    universe: pd.DataFrame,
    start: str,
    end: str | None = None,
    benchmark_symbol: str = "^NSEI",
) -> pd.DataFrame:
    records = [
        (yahoo_symbol(row.ticker), row.ticker, str(row.sector), True)
        for row in universe.itertuples(index=False)
    ]
    records.append((benchmark_symbol, "NIFTY50", "INDEX", False))
    panels: list[pd.DataFrame] = []
    failures: list[str] = []
    metadata = {vendor: (output, sector, member) for vendor, output, sector, member in records}
    for offset in range(0, len(records), 50):
        batch = [record[0] for record in records[offset:offset + 50]]
        raw = yf.download(
            batch,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=True,
            actions=False,
            progress=False,
            threads=True,
            timeout=20,
        )
        for vendor_ticker in batch:
            output_ticker, sector, member = metadata[vendor_ticker]
            frame = normalize_symbol_frame(raw, vendor_ticker, output_ticker, sector, member)
            if frame.empty:
                failures.append(vendor_ticker)
            else:
                panels.append(frame)
    if failures:
        failure_rate = len(failures) / len(records)
        print(f"Warning: Yahoo returned no valid candles for {len(failures)} symbols")
        print(", ".join(failures))
        if benchmark_symbol in failures or failure_rate > 0.05:
            raise RuntimeError(
                f"Download rejected: {failure_rate:.1%} of the universe is missing"
            )
    panel = pd.concat(panels, ignore_index=True)
    return panel.sort_values(["date", "ticker"]).drop_duplicates(["date", "ticker"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch adjusted NSE daily candles from Yahoo Finance")
    parser.add_argument(
        "--universe",
        default="midsmall400",
        help="Universe CSV or 'midsmall400' for the current official NSE index list",
    )
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end")
    parser.add_argument("--output", default="data/yahoo_india_panel.csv")
    args = parser.parse_args()

    universe = load_universe(args.universe)
    panel = download_panel(universe, args.start, args.end)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output, index=False)
    counts = panel.groupby("ticker").size()
    print(f"Wrote {len(panel):,} adjusted daily bars for {len(counts)} instruments -> {output}")
    print(f"Date range: {panel['date'].min().date()} to {panel['date'].max().date()}")
    print(f"Bars/instrument: min {counts.min():,}, median {int(counts.median()):,}, max {counts.max():,}")
    print("Research warning: a current universe used historically has survivorship bias.")


if __name__ == "__main__":
    main()
