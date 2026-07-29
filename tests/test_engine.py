import pandas as pd
import pytest
from india_leader_score import validate_panel


def test_rejects_impossible_candle():
    df = pd.DataFrame([{
        "date": "2025-01-01", "ticker": "ABC", "open": 100,
        "high": 90, "low": 80, "close": 95, "volume": 1000
    }])
    with pytest.raises(ValueError, match="impossible"):
        validate_panel(df)


def test_deduplicates_deterministically():
    df = pd.DataFrame([
        {"date":"2025-01-01","ticker":"abc","open":100,"high":102,"low":99,"close":101,"volume":1000},
        {"date":"2025-01-01","ticker":"abc","open":100,"high":103,"low":99,"close":102,"volume":1100},
    ])
    out = validate_panel(df)
    assert len(out) == 1
    assert out.iloc[0]["close"] == 102

