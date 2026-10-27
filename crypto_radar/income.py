"""Simple, assumption-based calculator for hypothetical crypto income."""
from __future__ import annotations


def calculate_income_scenario(
    principal: float,
    apr_pct: float,
    months: int,
    price_change_pct: float = 0.0,
    fee_pct: float = 0.0,
) -> dict[str, float]:
    """Estimate a hypothetical yield scenario; this is not a forecast.

    APR is treated as a nominal annual rate compounded monthly. The asset-price
    change is applied to principal plus rewards. Fee is a one-off percentage of
    the starting principal. Taxes, changing rates, lockups, defaults, depegs,
    and protocol/provider failures are not modeled.
    """
    if principal < 0:
        raise ValueError("Principal must be zero or greater.")
    if apr_pct < 0:
        raise ValueError("APR must be zero or greater.")
    if months < 0:
        raise ValueError("Months must be zero or greater.")
    if fee_pct < 0 or fee_pct >= 100:
        raise ValueError("Fee must be at least 0 and less than 100 percent.")
    if price_change_pct < -100:
        raise ValueError("Asset price change cannot be below -100 percent.")

    monthly_rate = (apr_pct / 100) / 12
    rewards = principal * ((1 + monthly_rate) ** months - 1)
    gross_balance = principal + rewards
    value_after_price_change = gross_balance * (1 + price_change_pct / 100)
    fees = principal * fee_pct / 100
    ending_value = max(value_after_price_change - fees, 0.0)

    return {
        "principal": float(principal),
        "rewards": float(rewards),
        "fees": float(fees),
        "ending_value": float(ending_value),
        "profit_loss": float(ending_value - principal),
        "return_pct": float((ending_value / principal - 1) * 100) if principal else 0.0,
    }


def build_scenarios(
    principal: float,
    apr_pct: float,
    months: int,
    fee_pct: float = 0.0,
) -> list[dict[str, float]]:
    """Compare the same hypothetical yield under several asset-price changes."""
    scenarios = []
    for price_change in (-50.0, -20.0, 0.0, 20.0):
        row = calculate_income_scenario(
            principal=principal,
            apr_pct=apr_pct,
            months=months,
            price_change_pct=price_change,
            fee_pct=fee_pct,
        )
        row["asset_price_change_pct"] = price_change
        scenarios.append(row)
    return scenarios
