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



def test_backtest_aligns_benchmark_after_sma_warmup_and_models_slippage():
    prices = sample_prices(days=120)
    result, metrics = run_backtest(prices, fast_window=5, slow_window=15, fee_pct=0.1, slippage_pct=0.2)
    assert result.index.min() >= prices.index[14]
    assert len(result["Strategy Equity"]) == len(result["Buy & Hold Equity"])
    assert metrics["comparison_bars"] == len(result)
    assert metrics["buy_hold_max_drawdown"] <= 0
    assert metrics["total_trading_costs_pct_initial_equity"] >= 0


def test_backtest_rejects_invalid_slippage():
    with pytest.raises(ValueError, match="Slippage"):
        run_backtest(sample_prices(days=80), fast_window=5, slow_window=15, slippage_pct=float("nan"))


def test_backtest_rejects_non_positive_prices():
    prices = pd.DataFrame({"Close": [0, -1, 2]}, index=pd.date_range("2025-01-01", periods=3))
    with pytest.raises(ValueError):
        run_backtest(prices)


def test_parameter_comparison_uses_chronological_train_and_test_periods():
    from crypto_radar.backtest import compare_sma_parameter_sets

    prices = sample_prices(days=240)
    table = compare_sma_parameter_sets(
        prices, [(5, 15), (10, 30), (20, 50)], train_fraction=0.7,
        fee_pct=0.1, slippage_pct=0.05,
    )
    assert len(table) == 3
    assert {"Train return (%)", "Test return (%)", "Test Buy & Hold (%)",
            "Test excess vs Buy & Hold (pp)", "Test max drawdown (%)",
            "Test position changes", "Train bars", "Test bars"}.issubset(table.columns)
    assert (table["Train bars"] > 0).all()
    assert (table["Test bars"] > 0).all()
    assert table["Test bars"].nunique() == 1
    assert table.iloc[0]["Test excess vs Buy & Hold (pp)"] >= table.iloc[-1]["Test excess vs Buy & Hold (pp)"]


def test_parameter_comparison_rejects_invalid_split():
    from crypto_radar.backtest import compare_sma_parameter_sets

    with pytest.raises(ValueError, match="Train fraction"):
        compare_sma_parameter_sets(sample_prices(days=100), [(5, 15)], train_fraction=0.4)

