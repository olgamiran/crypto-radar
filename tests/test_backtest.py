import pandas as pd
import pytest

from crypto_radar.backtest import compare_execution_cost_scenarios, run_backtest
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



def test_execution_cost_scenarios_use_same_history_and_increasing_costs():
    prices = sample_prices(days=180)
    table = compare_execution_cost_scenarios(
        prices, fast_window=5, slow_window=15, fee_pct=0.1, slippage_pct=0.05
    )
    assert table["Scenario"].tolist() == [
        "Base costs (1×)", "Double costs (2×)", "High costs (4×)"
    ]
    assert table["Comparison bars"].nunique() == 1
    assert table["Position changes"].nunique() == 1
    assert table["Fee per change (%)"].tolist() == [0.1, 0.2, 0.4]
    assert table["Slippage per change (%)"].tolist() == [0.05, 0.1, 0.2]
    assert table["Strategy return (%)"].iloc[0] >= table["Strategy return (%)"].iloc[1]
    assert table["Strategy return (%)"].iloc[1] >= table["Strategy return (%)"].iloc[2]


def test_walk_forward_has_strictly_ordered_nonoverlapping_holdouts():
    from crypto_radar.backtest import walk_forward_sma_evaluation

    prices = sample_prices(days=240)
    table = walk_forward_sma_evaluation(prices, [(5, 15), (10, 30)], n_folds=3)
    assert len(table) == 3
    assert table["Fold"].tolist() == [1, 2, 3]
    assert table["Test bars"].sum() == 120
    assert (table["Train bars"].diff().dropna() > 0).all()
    for _, row in table.iterrows():
        assert row["Train end"] < row["Test start"] <= row["Test end"]
        assert (row["Selected fast SMA"], row["Selected slow SMA"]) in [(5, 15), (10, 30)]
    assert all(
        table.iloc[i]["Test end"] < table.iloc[i + 1]["Test start"]
        for i in range(len(table) - 1)
    )


def test_walk_forward_selection_ignores_future_price_changes():
    from crypto_radar.backtest import walk_forward_sma_evaluation

    prices = sample_prices(days=240)
    altered = prices.copy()
    altered.loc[altered.index[120]:, "Close"] *= 1.25
    original = walk_forward_sma_evaluation(prices, [(5, 15), (10, 30)], n_folds=3)
    changed = walk_forward_sma_evaluation(altered, [(5, 15), (10, 30)], n_folds=3)
    assert original.loc[0, "Selected fast SMA"] == changed.loc[0, "Selected fast SMA"]
    assert original.loc[0, "Selected slow SMA"] == changed.loc[0, "Selected slow SMA"]
    assert original.loc[0, "Train return (%)"] == pytest.approx(changed.loc[0, "Train return (%)"])


def test_walk_forward_rejects_insufficient_history():
    from crypto_radar.backtest import walk_forward_sma_evaluation

    with pytest.raises(ValueError, match="120"):
        walk_forward_sma_evaluation(sample_prices(days=100), [(5, 15)])


def test_walk_forward_stability_counts_and_selection_frequency():
    from crypto_radar.backtest import summarize_walk_forward_stability

    folds = pd.DataFrame({
        "Fold": [1, 2, 3],
        "Selected fast SMA": [5, 10, 5],
        "Selected slow SMA": [15, 30, 15],
        "Test return (%)": [-4.0, 2.0, 8.0],
        "Test Buy & Hold (%)": [-3.0, 1.0, 9.0],
        "Test excess vs Buy & Hold (pp)": [-1.0, 1.0, -1.0],
    })
    summary, frequency = summarize_walk_forward_stability(folds)
    assert summary["profitable_folds"] == 2
    assert summary["outperforming_folds"] == 1
    assert summary["worst_fold_return_pct"] == -4.0
    assert summary["best_fold_return_pct"] == 8.0
    assert summary["return_range_pp"] == 12.0
    assert summary["distinct_sma_pairs"] == 2
    assert summary["most_selected_pair_folds"] == 2
    assert frequency["Folds selected"].tolist() == [2, 1]


def test_walk_forward_stability_rejects_missing_values():
    from crypto_radar.backtest import summarize_walk_forward_stability

    folds = pd.DataFrame({
        "Fold": [1], "Selected fast SMA": [5], "Selected slow SMA": [15],
        "Test return (%)": [float("nan")], "Test Buy & Hold (%)": [1.0],
        "Test excess vs Buy & Hold (pp)": [0.0],
    })
    with pytest.raises(ValueError, match="missing"):
        summarize_walk_forward_stability(folds)
