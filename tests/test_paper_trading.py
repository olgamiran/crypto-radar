import pandas as pd
import pytest

from crypto_radar.data import sample_prices
from crypto_radar.paper_trading import simulate_sma_paper_trades


def test_paper_trading_returns_equity_and_trade_journal():
    equity, trades, metrics = simulate_sma_paper_trades(
        sample_prices(days=180), fast_window=5, slow_window=15,
        starting_cash=1000, fee_pct=0.1, slippage_pct=0.05,
    )
    assert not equity.empty
    assert {"Equity", "Drawdown", "Action"}.issubset(equity.columns)
    assert {"date", "action", "price", "quantity", "fee"}.issubset(trades.columns)
    assert metrics["starting_cash"] == 1000
    assert metrics["final_equity"] >= 0
    assert metrics["trade_count"] == len(trades)
    assert metrics["fees_paid"] >= 0


def test_paper_trading_rejects_invalid_windows_and_costs():
    prices = sample_prices(days=80)
    with pytest.raises(ValueError):
        simulate_sma_paper_trades(prices, 20, 20)
    with pytest.raises(ValueError, match="Slippage"):
        simulate_sma_paper_trades(prices, 5, 15, slippage_pct=float("nan"))


def test_paper_trading_handles_empty_cash_without_trades():
    equity, trades, metrics = simulate_sma_paper_trades(sample_prices(days=80), 5, 15, 0)
    assert metrics["final_equity"] == 0
    assert trades.empty



def test_paper_trading_compares_buy_and_hold_on_same_period():
    prices = sample_prices(days=120)
    equity, _, metrics = simulate_sma_paper_trades(
        prices, fast_window=5, slow_window=15, starting_cash=2000,
        fee_pct=0.1, slippage_pct=0.05,
    )
    assert "Buy & Hold Equity" in equity.columns
    assert "Buy & Hold Drawdown" in equity.columns
    assert equity["Buy & Hold Equity"].iloc[0] == pytest.approx(2000)
    assert metrics["buy_hold_final_equity"] == pytest.approx(equity["Buy & Hold Equity"].iloc[-1])
    assert metrics["excess_return_pct"] == pytest.approx(
        metrics["return_pct"] - metrics["buy_hold_return_pct"]
    )
    assert metrics["buy_hold_max_drawdown"] <= 0
