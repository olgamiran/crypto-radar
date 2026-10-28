"""Educational signal-based paper trading; no real orders are sent."""
from __future__ import annotations
import math
import pandas as pd


def simulate_sma_paper_trades(prices: pd.DataFrame, fast_window: int = 20,
                              slow_window: int = 50, starting_cash: float = 10000.0,
                              fee_pct: float = 0.1, slippage_pct: float = 0.05):
    if fast_window < 2 or slow_window < 3 or fast_window >= slow_window:
        raise ValueError("Require fast window >= 2 and smaller than slow window >= 3.")
    if not math.isfinite(float(starting_cash)) or starting_cash < 0:
        raise ValueError("Starting cash must be finite and non-negative.")
    for name, value in (("Fee", fee_pct), ("Slippage", slippage_pct)):
        if not math.isfinite(float(value)) or not 0 <= value < 100:
            raise ValueError(f"{name} must be finite and between 0 and 100 percent.")
    if "Close" not in prices:
        raise ValueError("Prices must contain a Close column.")
    data = prices[["Close"]].copy()
    data["Close"] = pd.to_numeric(data["Close"], errors="coerce")
    data = data.loc[data["Close"].notna() & (data["Close"] > 0)].sort_index()
    if data.empty:
        raise ValueError("Prices must contain positive close prices.")
    data = data.loc[~data.index.duplicated(keep="last")].copy()
    data["Fast SMA"] = data["Close"].rolling(fast_window).mean()
    data["Slow SMA"] = data["Close"].rolling(slow_window).mean()
    data["Signal"] = (data["Fast SMA"] > data["Slow SMA"]).astype(int).shift(1).fillna(0).astype(int)
    cash, units, ledger, rows = float(starting_cash), 0.0, [], []
    for date, row in data.iterrows():
        price, signal = float(row["Close"]), int(row["Signal"])
        action = "HOLD"
        if signal and units == 0 and cash > 0:
            px = price * (1 + slippage_pct / 100)
            units = cash / (px * (1 + fee_pct / 100))
            fee = units * px * fee_pct / 100
            cash = 0.0
            action = "BUY"
            ledger.append({"date": str(date), "action": action, "price": px, "quantity": units, "fee": fee})
        elif not signal and units > 0:
            px = price * (1 - slippage_pct / 100)
            gross = units * px
            fee = gross * fee_pct / 100
            cash += gross - fee
            ledger.append({"date": str(date), "action": "SELL", "price": px, "quantity": units, "fee": fee})
            units, action = 0.0, "SELL"
        buy_hold_equity = starting_cash * price / float(data["Close"].iloc[0])
        rows.append({"date": date, "Close": price, "Signal": signal, "Action": action,
                     "Cash": cash, "Units": units, "Equity": cash + units * price,
                     "Buy & Hold Equity": buy_hold_equity})
    equity = pd.DataFrame(rows).set_index("date")
    equity["Drawdown"] = equity["Equity"] / equity["Equity"].cummax() - 1
    equity["Buy & Hold Drawdown"] = equity["Buy & Hold Equity"] / equity["Buy & Hold Equity"].cummax() - 1
    trades = pd.DataFrame(ledger, columns=["date", "action", "price", "quantity", "fee"])
    final = float(equity["Equity"].iloc[-1])
    buy_hold_final = float(equity["Buy & Hold Equity"].iloc[-1])
    strategy_return = (final / starting_cash - 1) * 100 if starting_cash else 0.0
    buy_hold_return = (buy_hold_final / starting_cash - 1) * 100 if starting_cash else 0.0
    metrics = {"starting_cash": starting_cash, "final_equity": final,
               "buy_hold_final_equity": buy_hold_final,
               "buy_hold_return_pct": buy_hold_return,
               "excess_return_pct": strategy_return - buy_hold_return,
               "buy_hold_max_drawdown": float(equity["Buy & Hold Drawdown"].min()),
               "profit_loss": final - starting_cash,
               "return_pct": strategy_return,
               "max_drawdown": float(equity["Drawdown"].min()),
               "trade_count": float(len(trades)),
               "fees_paid": float(trades["fee"].sum()) if not trades.empty else 0.0}
    return equity, trades, metrics
