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
