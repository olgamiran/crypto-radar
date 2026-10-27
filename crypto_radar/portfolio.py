"""Virtual, in-memory portfolio ledger. No exchange or wallet integration."""
from __future__ import annotations

from typing import Any
import math

import pandas as pd

_TRANSACTION_TYPES = {"BUY", "SELL", "REWARD", "FEE"}


def build_portfolio_snapshot(
    starting_cash: float,
    transactions: list[dict[str, Any]],
    current_prices: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Replay a virtual transaction ledger and mark holdings to supplied prices.

    Transaction fields: type, asset, quantity, price_usd, fee_usd, date.
    BUY/SELL move cash and units; REWARD adds units without spending principal;
    FEE records a cash expense. All values are hypothetical USD amounts.
    """
    if not math.isfinite(float(starting_cash)) or starting_cash < 0:
        raise ValueError("Starting cash must be a finite number that is zero or greater.")

    prices = current_prices or {}
    for asset, price in prices.items():
        if not asset or not math.isfinite(float(price)) or float(price) < 0:
            raise ValueError("Current prices must have an asset name and finite non-negative value.")

    cash = float(starting_cash)
    holdings: dict[str, float] = {}
    last_prices: dict[str, float] = {}
    total_fees = 0.0
    ledger: list[dict[str, Any]] = []

    for index, raw in enumerate(transactions, start=1):
        tx_type = str(raw.get("type", "")).upper()
        asset = str(raw.get("asset", "")).strip()
        quantity = float(raw.get("quantity", 0.0))
        price = float(raw.get("price_usd", 0.0))
        fee = float(raw.get("fee_usd", 0.0))
        date = str(raw.get("date", ""))

        if tx_type not in _TRANSACTION_TYPES:
            raise ValueError(f"Transaction {index}: unsupported type.")
        if not all(math.isfinite(value) for value in (quantity, price, fee)) or fee < 0 or quantity < 0 or price < 0:
            raise ValueError(f"Transaction {index}: quantity, price, and fee must be finite and non-negative.")
        if tx_type != "FEE" and not asset:
            raise ValueError(f"Transaction {index}: asset is required.")
        if tx_type in {"BUY", "SELL", "REWARD"} and quantity <= 0:
            raise ValueError(f"Transaction {index}: quantity must be greater than zero.")
        if tx_type in {"BUY", "SELL"} and price <= 0:
            raise ValueError(f"Transaction {index}: price must be greater than zero.")
        if tx_type == "FEE" and fee <= 0:
            raise ValueError(f"Transaction {index}: fee must be greater than zero.")

        gross = quantity * price
        if tx_type == "BUY":
            total_cost = gross + fee
            if total_cost > cash + 1e-9:
                raise ValueError(f"Transaction {index}: insufficient virtual cash for this purchase.")
            cash -= total_cost
            holdings[asset] = holdings.get(asset, 0.0) + quantity
            last_prices[asset] = price
        elif tx_type == "SELL":
            available = holdings.get(asset, 0.0)
            if quantity > available + 1e-9:
                raise ValueError(f"Transaction {index}: cannot sell more units than the portfolio holds.")
            if gross < fee:
                raise ValueError(f"Transaction {index}: sale proceeds cannot be less than the fee.")
            cash += gross - fee
            holdings[asset] = max(available - quantity, 0.0)
            last_prices[asset] = price
        elif tx_type == "REWARD":
            holdings[asset] = holdings.get(asset, 0.0) + quantity
            last_prices[asset] = price
            cash -= fee
        else:  # FEE
            cash -= fee

        if cash < -1e-9:
            raise ValueError(f"Transaction {index}: fees exceed available virtual cash.")
        cash = max(cash, 0.0)
        total_fees += fee
        ledger.append({
            "date": date,
            "type": tx_type,
            "asset": asset or "—",
            "quantity": quantity,
            "price_usd": price,
            "value_usd": gross,
            "fee_usd": fee,
            "cash_after_usd": cash,
            "asset_units_after": holdings.get(asset, 0.0) if asset else 0.0,
        })

    position_rows: list[dict[str, float | str]] = []
    holdings_value = 0.0
    for asset, quantity in sorted(holdings.items()):
        if quantity <= 1e-12:
            continue
        mark_price = float(prices.get(asset, last_prices.get(asset, 0.0)))
        if mark_price < 0:
            raise ValueError(f"Current price for {asset} must be non-negative.")
        market_value = quantity * mark_price
        holdings_value += market_value
        position_rows.append({
            "asset": asset,
            "quantity": quantity,
            "price_usd": mark_price,
            "market_value_usd": market_value,
        })

    equity = cash + holdings_value
    profit_loss = equity - float(starting_cash)
    return {
        "starting_cash": float(starting_cash),
        "cash": cash,
        "holdings": holdings,
        "positions": pd.DataFrame(
            position_rows,
            columns=["asset", "quantity", "price_usd", "market_value_usd"],
        ),
        "ledger": pd.DataFrame(
            ledger,
            columns=[
                "date", "type", "asset", "quantity", "price_usd", "value_usd",
                "fee_usd", "cash_after_usd", "asset_units_after",
            ],
        ),
        "holdings_value": holdings_value,
        "equity": equity,
        "profit_loss": profit_loss,
        "return_pct": (profit_loss / starting_cash * 100) if starting_cash else 0.0,
        "total_fees": total_fees,
    }
