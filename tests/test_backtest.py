import pandas as pd
import pytest

from crypto_radar.backtest import run_backtest
from crypto_radar.data import sample_prices


def test_backtest_returns_expected_columns_and_metrics():
    prices = sample_prices(days=120)
    result, metrics = run_backtest(prices, fast_window=5, slow_window=15)
    assert "Strategy Equity" in result
    assert "Buy & Hold Equity" in result
    assert set(["strategy_return", "buy_hold_return", "max_drawdown", "sharpe_ratio"]).issubset(metrics)
    assert result["Strategy Equity"].notna().all()


def test_fast_must_be_less_than_slow():
    with pytest.raises(ValueError):
        run_backtest(sample_prices(days=80), fast_window=20, slow_window=20)


def test_missing_close_is_rejected():
    with pytest.raises(ValueError):
        run_backtest(pd.DataFrame({"Open": [1, 2, 3]}))
