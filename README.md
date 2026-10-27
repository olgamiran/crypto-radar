# Crypto Radar 📡

A beginner-friendly crypto market dashboard, backtesting lab, and **virtual crypto-income scenario calculator** built with Python, Pandas, and Streamlit.

> **Safety notice:** Educational software only. It does not provide financial advice, connect to wallets or exchanges, place trades, stake assets, or lend funds. Scenarios are hypothetical; rewards are not guaranteed and losses are possible.

## Features

- Daily price charts for BTC, ETH, SOL, XRP, and DOGE
- Public historical price data through Yahoo Finance when available
- Clearly labeled deterministic demo data when the live data source is unavailable
- SMA crossover backtest with adjustable windows and estimated fees
- Strategy-vs-buy-and-hold equity curves
- Return, CAGR, volatility, Sharpe ratio, maximum drawdown, and trade-count metrics
- Downloadable CSV of backtest output
- **Crypto Income Lab:** estimate hypothetical rewards using an assumed APR, duration, and one-off fee
- **Price stress test:** compare illustrative -50%, -20%, 0%, and +20% price-change scenarios
- Automated tests for the backtest and income calculator

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

## Crypto Income Lab assumptions

The calculator models a constant user-entered nominal APR compounded monthly. It applies a hypothetical asset-price change to the starting balance plus modeled rewards and subtracts a one-off fee based on the initial balance. It is deliberately simple and does **not** model taxes, changing rates, lock-up periods, liquidity constraints, stablecoin depegs, slashing, hacks, or provider/protocol failure. A positive yield can still result in an overall loss if the asset price falls.

The price paths are stress-test examples, not predictions or recommended allocations. Do not interpret the APR field as a live or verified offer.

## Strategy logic

The example strategy holds the asset when the fast simple moving average (SMA) is above the slow SMA, otherwise it stays in cash. Signals are shifted by one candle so the strategy does not use the same day's closing price to trade at that close. A configurable fee is applied when the position changes.

This is an educational daily-close model, not a production trading engine. It does not model spread, slippage, taxes, exchange outages, funding, liquidity, or order execution. Parameter tuning can overfit historical data.

## Project structure

```text
crypto-radar/
├── app.py
├── crypto_radar/
│   ├── __init__.py
│   ├── data.py
│   ├── backtest.py
│   └── income.py
├── tests/
│   ├── test_backtest.py
│   └── test_income.py
├── requirements.txt
├── pytest.ini
└── .gitignore
```

## Roadmap

- [x] Add a virtual crypto-income scenario calculator
- [x] Add illustrative price stress scenarios
- [ ] Add a virtual portfolio ledger (no wallet connection)
- [ ] Compare staking, lending, and holding with explicit risk notes
- [ ] Add historical yield inputs and clearly label data freshness/source
- [ ] Add walk-forward testing and train/test splits
- [ ] Add GitHub Actions for automated tests
- [ ] Publish a demo with Streamlit Community Cloud

## Risks and learning resources

Crypto staking, lending, and yield products can involve market, custody, technical, liquidity, counterparty, and regulatory risks. High advertised rates are not guarantees. Read the Austrian Financial Market Authority's overview before researching real products: [FMA Austria — Which crypto-assets and services are regulated?](https://www.fma.gv.at/en/investments/which-crypto-assets-and-services-are-regulated-and-which-are-not/).

## License

No license has been specified yet. Please add a license before allowing others to reuse or redistribute this project.
