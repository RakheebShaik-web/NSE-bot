import pandas as pd

from compare_caps import metrics


def test_metrics_reports_total_return_and_drawdown():
    trades = pd.DataFrame({"net_return": [0.1, -0.05]})
    equity = pd.DataFrame(
        {
            "date": ["2024-01-01", "2025-01-01"],
            "return": [0.1, -0.05],
            "equity": [1.1, 1.045],
        }
    )
    result = metrics("test", trades, equity)
    assert round(result["total_return"], 3) == 0.045
    assert round(result["max_drawdown"], 3) == -0.05
