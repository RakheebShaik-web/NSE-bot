import pandas as pd

from fetch_yahoo import normalize_symbol_frame, yahoo_symbol


def test_yahoo_symbol_adds_nse_suffix():
    assert yahoo_symbol("reliance") == "RELIANCE.NS"
    assert yahoo_symbol("^NSEI") == "^NSEI"


def test_normalize_symbol_frame_produces_strategy_schema():
    raw = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [104.0],
            "Low": [99.0],
            "Close": [103.0],
            "Volume": [1000],
        },
        index=pd.DatetimeIndex(["2026-07-30"], name="Date"),
    )
    result = normalize_symbol_frame(raw, "RELIANCE.NS", "RELIANCE", "Energy", True)
    assert list(result.columns) == [
        "date", "ticker", "open", "high", "low", "close", "volume", "sector", "in_universe"
    ]
    assert result.iloc[0]["ticker"] == "RELIANCE"
    assert bool(result.iloc[0]["in_universe"])
