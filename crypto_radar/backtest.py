"""Simple long-only moving-average crossover backtester."""
from __future__ import annotations

import pandas as pd


def run_backtest(prices: pd.DataFrame, fast_window: int = 20, slow_window: int = 50,
                 fee_pct: float = 0.1) -> tuple[pd.DataFrame, dict[str, float]]:
    """Run an SMA crossover strategy. Fees are charged on position changes.

    Signals are shifted by one bar to avoid using today's close to trade at that
    same close. Returns are a simplified daily-close model, not execution-grade.
    """
    if fast_window < 2 or slow_window < 3:
        raise ValueError("Moving-average windows must be at least 2 and 3 days.")
    if fast_window >= slow_window:
        raise ValueError("Fast window must be smaller than slow window.")
    if not 0 <= fee_pct < 100:
        raise ValueError("Fee must be between 0 and 100 percent.")
    if "Close" not in prices or prices["Close"].dropna().empty:
        raise ValueError("Prices must contain a non-empty Close column.")

    result = prices.copy()
    result["Fast SMA"] = result["Close"].rolling(fast_window).mean()
    result["Slow SMA"] = result["Close"].rolling(slow_window).mean()
    result["Signal"] = (result["Fast SMA"] > result["Slow SMA"]).astype(float)
    result["Position"] = result["Signal"].shift(1).fillna(0.0)
    result["Market Return"] = result["Close"].pct_change().fillna(0.0)
    result["Trades"] = result["Position"].diff().abs().fillna(result["Position"].abs())
    result["Strategy Return"] = result["Position"] * result["Market Return"] - result["Trades"] * (fee_pct / 100)
    result["Strategy Equity"] = (1 + result["Strategy Return"]).cumprod()
    result["Buy & Hold Equity"] = (1 + result["Market Return"]).cumprod()

    equity = result["Strategy Equity"]
    drawdown = equity / equity.cummax() - 1
    total_return = float(equity.iloc[-1] - 1)
    days = max((result.index[-1] - result.index[0]).days, 1)
    years = days / 365.25
    cagr = float(equity.iloc[-1] ** (1 / years) - 1) if equity.iloc[-1] > 0 else -1.0
    daily = result["Strategy Return"]
    volatility = float(daily.std(ddof=1) * (365 ** 0.5)) if len(daily) > 1 else 0.0
    mean_daily = float(daily.mean())
    std_daily = float(daily.std(ddof=1)) if len(daily) > 1 else 0.0
    sharpe = float(mean_daily / std_daily * (365 ** 0.5)) if std_daily > 0 else 0.0
    metrics = {
        "strategy_return": total_return,
        "buy_hold_return": float(result["Buy & Hold Equity"].iloc[-1] - 1),
        "max_drawdown": float(drawdown.min()),
        "annualized_volatility": volatility,
        "sharpe_ratio": sharpe,
        "cagr": cagr,
        "trade_count": float((result["Trades"] > 0).sum()),
    }
    return result, metrics
