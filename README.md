# Crypto Radar 📡

A beginner-friendly crypto market dashboard and strategy backtesting lab built with Python and Streamlit.

> **Disclaimer:** Educational software only. It does not provide financial advice or place trades. Backtests are simplified and can be misleading; past results do not predict future returns.

## Features

- Daily price charts for BTC, ETH, SOL, XRP, and DOGE
- Live public price history through Yahoo Finance when available
- Clearly labeled deterministic demo data when the live data source is unavailable
- SMA crossover strategy backtest with adjustable windows and estimated fees
- Strategy-vs-buy-and-hold equity curves
- Return, CAGR, volatility, Sharpe ratio, maximum drawdown, and trade-count metrics
- Downloadable CSV of the backtest output
- Automated tests for core backtest behavior

## Quick start

Requires Python 3.10 or newer.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`.

## Run tests

```bash
pytest -q
```

## Strategy logic

The example strategy buys/holds when the fast simple moving average (SMA) is above the slow SMA, otherwise it stays in cash. Signals are shifted by one candle so the strategy does not use the same day's closing price to trade at that close. A configurable fee is applied when the position changes.

This is an educational daily-close model, not a production trading engine. It does not model spread, slippage, taxes, exchange outages, funding, liquidity, or order execution. Parameter tuning can overfit historical data.

## Project structure

```text
crypto-radar/
├── app.py
├── crypto_radar/
│   ├── __init__.py
│   ├── data.py
│   └── backtest.py
├── tests/
│   └── test_backtest.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Roadmap

- [ ] Add RSI and MACD strategies
- [ ] Add portfolio allocation and transaction history
- [ ] Add alert rules and notifications
- [ ] Add walk-forward testing and train/test splits
- [ ] Add Docker support and CI with GitHub Actions
- [ ] Add more data providers and caching

## License

No license has been specified yet. Please add a license before allowing others to reuse or redistribute this project.
