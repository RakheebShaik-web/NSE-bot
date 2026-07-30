"""Compare identical strategy rules across official NSE cap segments."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import backtest
from fetch_yahoo import download_panel, load_universe
from india_leader_score import load_config

CAP_UNIVERSES = {
    "large_50": "nifty50",
    "large_100": ("nifty50", "next50"),
    "mid_150": "midcap150",
    "small_250": "smallcap250",
    "mid_small_400": "midsmall400",
    "broad_500": "nifty500",
}


def members(spec: str | tuple[str, ...]) -> pd.DataFrame:
    aliases = (spec,) if isinstance(spec, str) else spec
    frames = [load_universe(alias) for alias in aliases]
    return pd.concat(frames, ignore_index=True).drop_duplicates("ticker")


def metrics(
    name: str,
    trades: pd.DataFrame,
    equity: pd.DataFrame,
    holding_days: int = 10,
) -> dict:
    if equity.empty:
        return {"universe": name, "trades": 0}
    returns = equity["return"]
    curve = equity["equity"]
    start = pd.to_datetime(equity["date"].iloc[0])
    end = pd.to_datetime(equity["date"].iloc[-1])
    years = max((end - start).days / 365.25, 1 / 365.25)
    wins = trades.loc[trades["net_return"] > 0, "net_return"].sum()
    losses = -trades.loc[trades["net_return"] < 0, "net_return"].sum()
    return {
        "universe": name,
        "trades": int(len(trades)),
        "total_return": float(curve.iloc[-1] - 1),
        "cagr": float(curve.iloc[-1] ** (1 / years) - 1),
        "max_drawdown": float((curve / curve.cummax() - 1).min()),
        "win_rate": float((trades["net_return"] > 0).mean()),
        "sharpe": float(
            returns.mean() / returns.std() * np.sqrt(252 / holding_days)
        ) if returns.std() else 0.0,
        "profit_factor": float(wins / losses) if losses else None,
        "first_signal": str(start.date()),
        "last_signal": str(end.date()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--output-dir", default="output/cap_comparison")
    args = parser.parse_args()
    cfg = load_config()
    universes = {name: members(spec) for name, spec in CAP_UNIVERSES.items()}
    master = pd.concat(universes.values(), ignore_index=True).drop_duplicates("ticker")
    panel = download_panel(master, args.start)
    results = []
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name, universe in universes.items():
        allowed = set(universe["ticker"]) | {"NIFTY50"}
        subset = panel[panel["ticker"].isin(allowed)].copy()
        trades, equity = backtest(subset, cfg)
        trades.to_csv(output / f"{name}_trades.csv", index=False)
        equity.to_csv(output / f"{name}_equity.csv", index=False)
        results.append(metrics(name, trades, equity, cfg["holding_days"]))
    comparison = pd.DataFrame(results).sort_values(
        ["sharpe", "total_return"], ascending=False
    )
    comparison.to_csv(output / "comparison.csv", index=False)
    (output / "comparison.json").write_text(
        json.dumps(comparison.to_dict("records"), indent=2), encoding="utf-8"
    )
    print(comparison.to_string(index=False))
    print(f"\nComparison -> {output / 'comparison.csv'}")


if __name__ == "__main__":
    main()
