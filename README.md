# Crypto Radar 📡

A beginner-friendly crypto market dashboard, backtesting lab, and **virtual crypto-income research platform** built with Python, Pandas, and Streamlit.

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
- **Virtual Portfolio:** record simulated buys, sells, reward credits, and fees; mark positions to manually entered prices; review cash, holdings, equity, and profit/loss
- CSV export of the virtual transaction ledger
- **Yield Research:** compare buy-and-hold, native staking, centralized lending, DeFi lending, stablecoin yield, and liquidity provision with liquidity notes, qualitative risks, and due-diligence questions; no stale or invented APY claims
- Automated tests for the backtest, income calculator, portfolio accounting, and yield research catalogue
- GitHub Actions workflow configured to run tests on pushes and pull requests

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

### Run with Docker

```bash
docker build -t crypto-radar .
docker run --rm -p 8501:8501 crypto-radar
```

Then open `http://localhost:8501`. The container runs as a non-root user and includes a basic health check.

## Run tests

```bash
python -m pytest -q
```

## Virtual Portfolio accounting

The virtual portfolio starts with configurable simulated cash. A starting balance becomes locked after the first transaction to keep the ledger internally consistent.

- **BUY:** cash decreases by quantity × transaction price plus fees.
- **SELL:** cash increases by quantity × transaction price minus fees; selling more units than held is rejected.
- **REWARD:** adds units to holdings. The reward is not cash; its value depends on the entered price.
- **FEE:** records a standalone cash expense.
- Portfolio equity = virtual cash + the market value of held assets.
- Profit/loss = current portfolio equity minus starting virtual cash.

Prices are entered manually and are not live quotes. Transactions are stored in Streamlit session state, so the ledger may reset when the app session ends or the app restarts. CSV export is available for keeping a local copy. This is a simplified educational ledger, not tax accounting or a broker statement.

## Crypto Income Lab assumptions

The calculator models a constant user-entered nominal APR compounded monthly. It applies a hypothetical asset-price change to the starting balance plus modeled rewards and subtracts a one-off fee based on the initial balance. It does **not** model taxes, changing rates, lock-up periods, liquidity constraints, stablecoin depegs, slashing, hacks, or provider/protocol failure. A positive yield can still result in an overall loss if the asset price falls.

The price paths are stress-test examples, not predictions or recommended allocations. Do not interpret the APR field as a live or verified offer.

## Backtest assumptions

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
│   ├── income.py
│   ├── portfolio.py
│   └── yield_research.py
├── tests/
│   ├── test_backtest.py
│   ├── test_income.py
│   ├── test_portfolio.py
│   └── test_yield_research.py
├── .github/workflows/tests.yml
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── pytest.ini
├── .gitignore
├── CHANGELOG.md
└── LICENSE
```

## Roadmap

- [x] Add a virtual crypto-income scenario calculator
- [x] Add illustrative price stress scenarios
- [x] Add a virtual portfolio ledger with accounting validation
- [x] Add an educational yield-mechanism catalogue with risk notes
- [ ] Add explicit scenario comparison templates for staking, lending, stablecoins, and holding
- [ ] Add historical yield inputs with a source and timestamp for every rate
- [ ] Add walk-forward testing and train/test splits
- [ ] Add a persistent database for opt-in local portfolio history
- [x] Add Docker packaging for reproducible local runs
- [ ] Publish a demo with Streamlit Community Cloud

## Risks and learning resources

Crypto staking, lending, and yield products can involve market, custody, technical, liquidity, counterparty, and regulatory risks. High advertised rates are not guarantees. Read the Austrian Financial Market Authority's overview before researching real products: [FMA Austria — Which crypto-assets and services are regulated?](https://www.fma.gv.at/en/investments/which-crypto-assets-and-services-are-regulated-and-which-are-not/).

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
