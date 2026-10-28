"""Market data helpers with a live Yahoo Finance source and offline fallback."""
from __future__ import annotations

import numpy as np
import pandas as pd

SYMBOLS = {
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Solana (SOL)": "SOL-USD",
    "XRP": "XRP-USD",
    "Dogecoin (DOGE)": "DOGE-USD",
}


def sample_prices(symbol: str = "BTC-USD", days: int = 365, seed: int = 7) -> pd.DataFrame:
    """Generate deterministic sample OHLCV data for demos and offline use."""
    rng = np.random.default_rng(seed + sum(ord(c) for c in symbol))
    dates = pd.date_range(end=pd.Timestamp.now().normalize(), periods=days, freq="D")
    start = {"BTC-USD": 45000, "ETH-USD": 2400, "SOL-USD": 110}.get(symbol, 1.0)
    returns = rng.normal(0.0007, 0.035, size=days)
    close = start * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.008, size=days))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.025, size=days))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.025, size=days))
    volume = rng.integers(500_000, 8_000_000, size=days).astype(float)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)


def fetch_prices(symbol: str = "BTC-USD", period: str = "1y") -> tuple[pd.DataFrame, str]:
    """Fetch public daily candles; gracefully fall back to clearly labeled demo data."""
    try:
        import yfinance as yf
        data = yf.download(symbol, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        required = ["Open", "High", "Low", "Close", "Volume"]
        data = data[[c for c in required if c in data.columns]].dropna()
        if not data.empty and "Close" in data.columns:
            return data, "Live market data via Yahoo Finance"
    except Exception:
        pass
    days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}.get(period, 365)
    return sample_prices(symbol, days=days), "DEMO DATA — live source unavailable"


def assess_price_data(prices: pd.DataFrame) -> dict[str, object]:
    """Return transparent quality diagnostics for a daily crypto price series."""
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        return {
            "bars": 0, "start_date": None, "end_date": None,
            "invalid_close_rows": 0, "duplicate_timestamps": 0,
            "missing_calendar_days": 0, "max_gap_days": 0, "latest_age_days": None,
        }
    idx = pd.DatetimeIndex(pd.to_datetime(prices.index, errors="coerce"))
    valid_dates = ~idx.isna()
    idx = idx[valid_dates]
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    close = pd.to_numeric(prices.loc[valid_dates, "Close"], errors="coerce") if "Close" in prices else pd.Series(dtype=float)
    invalid_close = int((close.isna() | (close <= 0)).sum()) if len(close) else len(prices)
    duplicate_count = int(idx.duplicated(keep="last").sum())
    unique_dates = idx[~idx.duplicated(keep="last")].sort_values()
    gaps = unique_dates.to_series().diff().dt.days.dropna()
    missing_days = int((gaps - 1).clip(lower=0).sum()) if len(gaps) else 0
    max_gap = int(gaps.max()) if len(gaps) else 0
    latest = unique_dates[-1] if len(unique_dates) else None
    today_utc = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    age_days = max(0, int((today_utc - latest.normalize()).days)) if latest is not None else None
    return {
        "bars": int(len(prices)),
        "start_date": str(unique_dates[0].date()) if len(unique_dates) else None,
        "end_date": str(latest.date()) if latest is not None else None,
        "invalid_close_rows": invalid_close,
        "duplicate_timestamps": duplicate_count,
        "missing_calendar_days": missing_days,
        "max_gap_days": max_gap,
        "latest_age_days": age_days,
    }

