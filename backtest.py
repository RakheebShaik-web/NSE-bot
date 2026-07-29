"""Portfolio backtest with T-close signal and T+1-open execution."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from india_leader_score import load_config, build_features, score_signals


def backtest(panel: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = build_features(panel, cfg["benchmark"])
    signals = score_signals(features, cfg)
    prices = features.set_index(["date", "ticker"]).sort_index()
    calendar = sorted(features["date"].unique())
    date_pos = {d: i for i, d in enumerate(calendar)}
    # Use non-overlapping cohorts. This keeps gross exposure at or below 100%
    # without pretending that a fresh fully invested portfolio is available
    # on every signal date while prior positions are still open.
    cohort_dates = []
    next_allowed = 0
    for d in sorted(signals["date"].unique()):
        i = date_pos[d]
        if i >= next_allowed:
            cohort_dates.append(d)
            next_allowed = i + cfg["holding_days"] + 1
    signals = signals[signals["date"].isin(cohort_dates)]
    trades = []
    cost = cfg["round_trip_cost_bps"] / 10000

    for _, s in signals.iterrows():
        i = date_pos.get(s["date"])
        if i is None or i + 1 >= len(calendar):
            continue
        future_dates = calendar[i + 1:i + 1 + cfg["holding_days"]]
        try:
            entry = float(prices.loc[(future_dates[0], s["ticker"]), "open"])
        except KeyError:
            continue
        stop = entry - cfg["atr_stop_multiple"] * float(s["atr20"])
        highest = entry
        exit_price = exit_date = reason = None
        for d in future_dates:
            try:
                bar = prices.loc[(d, s["ticker"])]
            except KeyError:
                continue
            # Gap through stop fills at open; otherwise stop price.
            if float(bar["open"]) <= stop:
                exit_price, exit_date, reason = float(bar["open"]), d, "gap_stop"
                break
            if float(bar["low"]) <= stop:
                exit_price, exit_date, reason = stop, d, "trailing_stop"
                break
            highest = max(highest, float(bar["high"]))
            stop = max(stop, highest - cfg["atr_stop_multiple"] * float(s["atr20"]))
            exit_price, exit_date, reason = float(bar["close"]), d, "time_exit"
        if exit_price is None:
            continue
        gross = exit_price / entry - 1
        trades.append({
            "signal_date": s["date"], "entry_date": future_dates[0], "exit_date": exit_date,
            "ticker": s["ticker"], "sector": s["sector"], "score": s["leader_score_india"],
            "entry": entry, "exit": exit_price, "gross_return": gross,
            "net_return": gross - cost, "exit_reason": reason,
        })

    tr = pd.DataFrame(trades)
    if tr.empty:
        return tr, pd.DataFrame(columns=["date", "return", "equity"])
    # Conservative cohort portfolio: equal-weight signals by signal date.
    daily = tr.groupby("signal_date")["net_return"].mean().sort_index()
    equity = (1 + daily).cumprod()
    eq = pd.DataFrame({"date": daily.index, "return": daily.values, "equity": equity.values})
    return tr, eq


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output-dir", default="output/backtest")
    p.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
    args = p.parse_args()
    cfg = load_config(args.config)
    panel = pd.read_csv(args.input)
    trades, equity = backtest(panel, cfg)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "trades.csv", index=False)
    equity.to_csv(out / "equity.csv", index=False)
    summary = {"trades": len(trades)}
    if not equity.empty:
        r = equity["return"]
        peak = equity["equity"].cummax()
        summary.update({
            "final_multiple": float(equity["equity"].iloc[-1]),
            "max_drawdown": float((equity["equity"] / peak - 1).min()),
            "win_rate": float((trades["net_return"] > 0).mean()),
            "cohort_sharpe": float(r.mean() / r.std() * np.sqrt(252 / cfg["holding_days"])) if r.std() else 0,
        })
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
