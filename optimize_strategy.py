"""Purged expanding walk-forward research for the Midcap 150 strategy."""
from __future__ import annotations

import argparse
import copy
import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import backtest_features
from india_leader_score import build_features, load_config


def candidate_configs(base: dict) -> list[dict]:
    weight_sets = {
        "balanced": base["weights"],
        "faster": {
            "mom_126_21_pct": 0.40, "mom_252_21_pct": 0.10,
            "mom_63_pct": 0.20, "rs_20_pct": 0.15,
            "rvol_20_pct": 0.10, "liquidity_pct": 0.025,
            "low_vol_pct": 0.025,
        },
        "steadier": {
            "mom_126_21_pct": 0.25, "mom_252_21_pct": 0.30,
            "mom_63_pct": 0.10, "rs_20_pct": 0.10,
            "rvol_20_pct": 0.05, "liquidity_pct": 0.10,
            "low_vol_pct": 0.10,
        },
    }
    variants = []
    for holding, atr, threshold, breadth, weight_name in product(
        [10, 20], [2.5, 3.5], [80, 85, 90], [0.45, 0.55], weight_sets
    ):
        cfg = copy.deepcopy(base)
        cfg.update(
            holding_days=holding,
            atr_stop_multiple=atr,
            signal_threshold=threshold,
            top_n=5,
        )
        cfg["regime"]["breadth_minimum"] = breadth
        cfg["weights"] = weight_sets[weight_name]
        cfg["candidate"] = (
            f"h{holding}_atr{atr}_s{threshold}_b{breadth}_{weight_name}"
        )
        variants.append(cfg)
    return variants


def period_metrics(
    trades: pd.DataFrame, equity: pd.DataFrame, start: str, end: str, holding: int
) -> dict:
    if equity.empty:
        return {"return": -1.0, "sharpe": -99.0, "max_dd": -1.0, "trades": 0}
    dates = pd.to_datetime(equity["date"])
    mask = (dates >= start) & (dates < end)
    returns = equity.loc[mask, "return"]
    period_trades = trades[
        (pd.to_datetime(trades["signal_date"]) >= start)
        & (pd.to_datetime(trades["signal_date"]) < end)
    ]
    if len(returns) < 3:
        return {"return": -1.0, "sharpe": -99.0, "max_dd": -1.0, "trades": len(period_trades)}
    curve = (1 + returns).cumprod()
    sharpe = returns.mean() / returns.std() * np.sqrt(252 / holding) if returns.std() else 0
    return {
        "return": float(curve.iloc[-1] - 1),
        "sharpe": float(sharpe),
        "max_dd": float((curve / curve.cummax() - 1).min()),
        "trades": int(len(period_trades)),
    }


def selection_score(stats: dict) -> float:
    """Reward risk-adjusted performance; reject sparse or catastrophic trials."""
    if stats["trades"] < 80 or stats["max_dd"] < -0.35:
        return -999.0
    return stats["sharpe"] + 0.35 * stats["return"] + 0.5 * stats["max_dd"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/yahoo_midcap150_panel.csv")
    parser.add_argument("--output-dir", default="output/walk_forward")
    args = parser.parse_args()
    base = load_config()
    panel = pd.read_csv(args.input)
    features = build_features(panel, base["benchmark"])
    trials = []
    for cfg in candidate_configs(base):
        trades, equity = backtest_features(features, cfg)
        trials.append((cfg, trades, equity))

    folds = [
        ("2019-01-01", "2022-01-01", "2022-01-15", "2023-01-01"),
        ("2019-01-01", "2023-01-01", "2023-01-15", "2024-01-01"),
        ("2019-01-01", "2024-01-01", "2024-01-15", "2025-01-01"),
        ("2019-01-01", "2025-01-01", "2025-01-15", "2026-01-01"),
        ("2019-01-01", "2026-01-01", "2026-01-15", "2026-07-30"),
    ]
    fold_rows, oos_returns = [], []
    selections: dict[str, int] = {}
    for train_start, train_end, test_start, test_end in folds:
        ranked = []
        for cfg, trades, equity in trials:
            train = period_metrics(
                trades, equity, train_start, train_end, cfg["holding_days"]
            )
            ranked.append((selection_score(train), cfg, trades, equity, train))
        _, cfg, trades, equity, train = max(ranked, key=lambda row: row[0])
        test = period_metrics(trades, equity, test_start, test_end, cfg["holding_days"])
        selections[cfg["candidate"]] = selections.get(cfg["candidate"], 0) + 1
        fold_rows.append(
            {
                "train_end": train_end,
                "test_start": test_start,
                "test_end": test_end,
                "selected": cfg["candidate"],
                **{f"train_{k}": v for k, v in train.items()},
                **{f"test_{k}": v for k, v in test.items()},
            }
        )
        dates = pd.to_datetime(equity["date"])
        oos_returns.extend(
            equity.loc[(dates >= test_start) & (dates < test_end), "return"].tolist()
        )

    oos = pd.Series(oos_returns, dtype=float)
    curve = (1 + oos).cumprod()
    oos_summary = {
        "return": float(curve.iloc[-1] - 1),
        "max_drawdown": float((curve / curve.cummax() - 1).min()),
        "sharpe": float(oos.mean() / oos.std() * np.sqrt(252 / base["holding_days"])),
        "observations": int(len(oos)),
        "selections": selections,
        "trials": len(trials),
    }
    winner = max(selections, key=selections.get)
    winner_cfg, winner_trades, winner_equity = next(
        (cfg, trades, equity)
        for cfg, trades, equity in trials
        if cfg["candidate"] == winner
    )
    full = period_metrics(
        winner_trades, winner_equity, "2019-01-01", "2026-07-30",
        winner_cfg["holding_days"]
    )
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(fold_rows).to_csv(output / "folds.csv", index=False)
    winner_trades.to_csv(output / "winner_trades.csv", index=False)
    winner_equity.to_csv(output / "winner_equity.csv", index=False)
    report = {"winner": winner, "config": winner_cfg, "walk_forward": oos_summary, "full": full}
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
