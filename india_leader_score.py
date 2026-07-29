"""Leakage-safe Indian equity momentum research and signal engine.

Input is a point-in-time panel CSV with:
date,ticker,open,high,low,close,volume,sector,in_universe

Benchmark rows use ticker=NIFTY50. Prices must be split/bonus adjusted and
volume must be unadjusted or consistently back-adjusted by the data vendor.
Signals formed at close on T are executable at open on T+1.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


def load_config(path: str | Path = ROOT / "config.json") -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_panel(df: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "ticker", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
    out = out.sort_values(["ticker", "date"]).drop_duplicates(["date", "ticker"], keep="last")
    numeric = ["open", "high", "low", "close", "volume"]
    out[numeric] = out[numeric].apply(pd.to_numeric, errors="coerce")
    impossible = (
        (out["high"] < out[["open", "close", "low"]].max(axis=1))
        | (out["low"] > out[["open", "close", "high"]].min(axis=1))
        | (out[numeric] < 0).any(axis=1)
    )
    if impossible.any():
        raise ValueError(f"{int(impossible.sum())} impossible OHLCV rows")
    if "sector" not in out:
        out["sector"] = "UNKNOWN"
    if "in_universe" not in out:
        out["in_universe"] = True
    return out.dropna(subset=numeric)


def _pct_rank(df: pd.DataFrame, col: str, ascending: bool = True) -> pd.Series:
    return df.groupby("date")[col].rank(pct=True, ascending=ascending) * 100


def build_features(panel: pd.DataFrame, benchmark: str = "NIFTY50") -> pd.DataFrame:
    df = validate_panel(panel)
    g = df.groupby("ticker", group_keys=False)
    prev = g["close"].shift(1)
    tr = pd.concat(
        [(df["high"] - df["low"]), (df["high"] - prev).abs(), (df["low"] - prev).abs()],
        axis=1,
    ).max(axis=1)
    df["atr20"] = tr.groupby(df["ticker"]).transform(lambda s: s.rolling(20, min_periods=20).mean())
    df["ret20"] = g["close"].pct_change(20)
    df["mom63"] = g["close"].pct_change(63)
    # Skip the most recent month to reduce short-term reversal contamination.
    df["mom126_21"] = g["close"].shift(21) / g["close"].shift(126) - 1
    df["mom252_21"] = g["close"].shift(21) / g["close"].shift(252) - 1
    daily_ret = g["close"].pct_change()
    df["vol63"] = daily_ret.groupby(df["ticker"]).transform(
        lambda s: s.rolling(63, min_periods=50).std() * np.sqrt(252)
    )
    df["rvol20"] = df["volume"] / g["volume"].transform(
        lambda s: s.shift(1).rolling(20, min_periods=15).median()
    )
    df["traded_value"] = df["close"] * df["volume"]
    df["median_value20"] = df.groupby("ticker")["traded_value"].transform(
        lambda s: s.shift(1).rolling(20, min_periods=15).median()
    )
    df["sma50"] = g["close"].transform(lambda s: s.rolling(50, min_periods=50).mean())
    df["sma200"] = g["close"].transform(lambda s: s.rolling(200, min_periods=200).mean())

    bench = df[df["ticker"] == benchmark][["date", "ret20", "close", "sma50", "sma200"]].rename(
        columns={"ret20": "benchmark_ret20", "close": "benchmark_close",
                 "sma50": "benchmark_sma50", "sma200": "benchmark_sma200"}
    )
    df = df.merge(bench, on="date", how="left")
    df["rs20"] = df["ret20"] - df["benchmark_ret20"]

    stocks = df["ticker"] != benchmark
    eligible = stocks & df["in_universe"].fillna(False)
    rank_defs = {
        "mom_126_21_pct": ("mom126_21", True),
        "mom_252_21_pct": ("mom252_21", True),
        "mom_63_pct": ("mom63", True),
        "rs_20_pct": ("rs20", True),
        "rvol_20_pct": ("rvol20", True),
        "liquidity_pct": ("median_value20", True),
        "low_vol_pct": ("vol63", False),
    }
    for target, (source, ascending) in rank_defs.items():
        df[target] = np.nan
        df.loc[eligible, target] = _pct_rank(df.loc[eligible], source, ascending)

    breadth = (
        df.loc[eligible].assign(above200=lambda x: x["close"] > x["sma200"])
        .groupby("date")["above200"].mean().rename("breadth_above_200")
    )
    return df.merge(breadth, on="date", how="left")


def score_signals(features: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    cfg = config or load_config()
    df = features.copy()
    weights = cfg["weights"]
    if not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("Feature weights must sum to 1.0")
    missing = set(weights) - set(df)
    if missing:
        raise ValueError(f"Missing ranked features: {sorted(missing)}")
    df["leader_score_india"] = sum(df[col].fillna(50.0) * weight for col, weight in weights.items())
    regime = (
        (df["benchmark_close"] > df["benchmark_sma200"])
        & (df["benchmark_sma50"] > df["benchmark_sma200"])
        & (df["breadth_above_200"] >= cfg["regime"]["breadth_minimum"])
    )
    liquid = (
        (df["close"] >= cfg["minimum_price_inr"])
        & (df["median_value20"] >= cfg["minimum_median_traded_value_inr"])
    )
    valid = (
        (df["ticker"] != cfg["benchmark"])
        & df["in_universe"].fillna(False)
        & regime & liquid
        & (df["leader_score_india"] >= cfg["signal_threshold"])
    )
    out = df.loc[valid].copy()
    out = out.sort_values(["date", "leader_score_india"], ascending=[True, False])
    out["rank"] = out.groupby("date").cumcount() + 1
    out = out[out["rank"] <= cfg["top_n"]]
    out["initial_stop"] = out["close"] - cfg["atr_stop_multiple"] * out["atr20"]
    out["signal_date"] = out["date"]
    return out


def run_pipeline(input_csv: str | Path, output_csv: str | Path, config_path: str | Path = ROOT / "config.json"):
    cfg = load_config(config_path)
    raw = pd.read_csv(input_csv)
    features = build_features(raw, cfg["benchmark"])
    signals = score_signals(features, cfg)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    signals.to_csv(output_csv, index=False)
    return features, signals
