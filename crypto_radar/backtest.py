"""Long-only SMA crossover backtest with aligned benchmark and execution costs."""
from __future__ import annotations

import math
import pandas as pd


def _max_drawdown(equity: pd.Series) -> float:
    return float((equity / equity.cummax() - 1.0).min())


def run_backtest(
    prices: pd.DataFrame,
    fast_window: int = 20,
    slow_window: int = 50,
    fee_pct: float = 0.1,
    slippage_pct: float = 0.05,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Backtest an SMA strategy and buy-and-hold over identical valid dates.

    Fee and slippage are charged on each position change. Signals execute from
    the next bar (one-bar lag); the model remains a simplified daily-close
    approximation and does not simulate order books or taxes.
    """
    if fast_window < 2 or slow_window < 3:
        raise ValueError("Moving-average windows must be at least 2 and 3 days.")
    if fast_window >= slow_window:
        raise ValueError("Fast window must be smaller than slow window.")
    for name, value in (("Fee", fee_pct), ("Slippage", slippage_pct)):
        if not math.isfinite(float(value)) or not 0 <= value < 100:
            raise ValueError(f"{name} must be finite and between 0 and 100 percent.")
    if "Close" not in prices:
        raise ValueError("Prices must contain a non-empty Close column.")
    result = prices.copy()
    result["Close"] = pd.to_numeric(result["Close"], errors="coerce")
    result = result.loc[result["Close"].notna() & (result["Close"] > 0)].sort_index()
    if result.empty:
        raise ValueError("Prices must contain a non-empty Close column with positive prices.")
    result = result.loc[~result.index.duplicated(keep="last")].copy()
    result["Fast SMA"] = result["Close"].rolling(fast_window, min_periods=fast_window).mean()
    result["Slow SMA"] = result["Close"].rolling(slow_window, min_periods=slow_window).mean()
    result["Signal"] = (result["Fast SMA"] > result["Slow SMA"]).astype(float)
    result["Position"] = result["Signal"].shift(1).fillna(0.0)
    # Compare both approaches only once the slow SMA is available.
    first_valid = result["Slow SMA"].first_valid_index()
    if first_valid is None:
        raise ValueError(f"Not enough price history for the slow window ({slow_window} bars required).")
    result = result.loc[first_valid:].copy()
    result["Market Return"] = result["Close"].pct_change().fillna(0.0)
    result["Trades"] = result["Position"].diff().abs().fillna(result["Position"].abs())
    cost_rate = (fee_pct + slippage_pct) / 100.0
    result["Trading Costs"] = result["Trades"] * cost_rate
    result["Strategy Return"] = result["Position"] * result["Market Return"] - result["Trading Costs"]
    result["Buy & Hold Return"] = result["Market Return"]
    result["Strategy Equity"] = (1 + result["Strategy Return"]).cumprod()
    result["Buy & Hold Equity"] = (1 + result["Buy & Hold Return"]).cumprod()
    equity = result["Strategy Equity"]
    daily = result["Strategy Return"]
    years = max((result.index[-1] - result.index[0]).days / 365.25, 1 / 365.25)
    total_return = float(equity.iloc[-1] - 1)
    volatility = float(daily.std(ddof=1) * math.sqrt(365)) if len(daily) > 1 else 0.0
    std_daily = float(daily.std(ddof=1)) if len(daily) > 1 else 0.0
    metrics = {
        "strategy_return": total_return,
        "buy_hold_return": float(result["Buy & Hold Equity"].iloc[-1] - 1),
        "max_drawdown": _max_drawdown(equity),
        "buy_hold_max_drawdown": _max_drawdown(result["Buy & Hold Equity"]),
        "annualized_volatility": volatility,
        "sharpe_ratio": float(daily.mean() / std_daily * math.sqrt(365)) if std_daily > 0 else 0.0,
        "cagr": float(equity.iloc[-1] ** (1 / years) - 1) if equity.iloc[-1] > 0 else -1.0,
        "trade_count": float((result["Trades"] > 0).sum()),
        "total_trading_costs_pct_initial_equity": float(result["Trading Costs"].sum() * 100),
        "comparison_start": str(result.index[0]),
        "comparison_end": str(result.index[-1]),
        "comparison_bars": float(len(result)),
    }
    return result, metrics


def compare_sma_parameter_sets(
    prices: pd.DataFrame,
    configurations: list[tuple[int, int]],
    train_fraction: float = 0.7,
    fee_pct: float = 0.1,
    slippage_pct: float = 0.05,
) -> pd.DataFrame:
    """Compare fixed SMA configurations on chronological train/test periods.

    The split date is based on the cleaned raw price history, not each
    configuration's indicator warm-up. Test returns are compounded only from
    bars on/after the split date; the signal on those bars may use earlier
    prices, as it would in a real walk-forward evaluation.
    """
    if not math.isfinite(float(train_fraction)) or not 0.5 <= train_fraction <= 0.9:
        raise ValueError("Train fraction must be between 0.5 and 0.9.")
    if "Close" not in prices:
        raise ValueError("Prices must contain a Close column.")
    clean = prices[["Close"]].copy()
    clean["Close"] = pd.to_numeric(clean["Close"], errors="coerce")
    clean = clean.loc[clean["Close"].notna() & (clean["Close"] > 0)].sort_index()
    clean = clean.loc[~clean.index.duplicated(keep="last")]
    if len(clean) < 20:
        raise ValueError("At least 20 valid price bars are required for a parameter comparison.")
    if not configurations:
        raise ValueError("Provide at least one SMA configuration.")
    split_pos = min(max(int(len(clean) * train_fraction), 1), len(clean) - 1)
    split_date = clean.index[split_pos]
    rows = []
    for fast_window, slow_window in configurations:
        result, _ = run_backtest(clean, fast_window, slow_window, fee_pct, slippage_pct)
        train = result.loc[result.index < split_date]
        test = result.loc[result.index >= split_date]
        if len(train) < 2 or len(test) < 2:
            continue
        train_return = float((1 + train["Strategy Return"]).prod() - 1)
        test_return = float((1 + test["Strategy Return"]).prod() - 1)
        test_buy_hold = float((1 + test["Buy & Hold Return"]).prod() - 1)
        test_equity = (1 + test["Strategy Return"]).cumprod()
        test_drawdown = float((test_equity / test_equity.cummax() - 1).min())
        rows.append({
            "Fast SMA": fast_window,
            "Slow SMA": slow_window,
            "Train return (%)": train_return * 100,
            "Test return (%)": test_return * 100,
            "Test Buy & Hold (%)": test_buy_hold * 100,
            "Test excess vs Buy & Hold (pp)": (test_return - test_buy_hold) * 100,
            "Test max drawdown (%)": test_drawdown * 100,
            "Test position changes": int((test["Trades"] > 0).sum()),
            "Train bars": int(len(train)),
            "Test bars": int(len(test)),
        })
    if not rows:
        raise ValueError("Not enough data remains in both periods for these SMA settings.")
    return pd.DataFrame(rows).sort_values(
        ["Test excess vs Buy & Hold (pp)", "Test return (%)"], ascending=False
    ).reset_index(drop=True)

