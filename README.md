# Crypto Radar 📡

A beginner-friendly crypto market dashboard, backtesting lab, and **virtual crypto-income research platform** built with Python, Pandas, and Streamlit.

> **Safety notice:** Educational software only. It does not provide financial advice, connect to wallets or exchanges, place trades, stake assets, or lend funds. Scenarios are hypothetical; rewards are not guaranteed and losses are possible.

## Features

- Daily price charts for BTC, ETH, SOL, XRP, and DOGE
- Public historical price data through Yahoo Finance when available
- Clearly labeled deterministic demo data when the live data source is unavailable
- SMA crossover backtest with adjustable windows, fees, and estimated slippage
- Fair strategy-versus-buy-and-hold comparison after the moving-average warm-up period
- Drawdown for strategy and benchmark, comparison dates, volatility, Sharpe ratio, CAGR, and trade count
- Signal-driven historical paper trading with virtual cash, simulated trade journal, equity curve, same-period buy-and-hold benchmark, and CSV export
- Strategy-vs-buy-and-hold equity curves
- Return, CAGR, volatility, Sharpe ratio, maximum drawdown, and trade-count metrics
- Downloadable CSV of backtest output
- **Crypto Income Lab:** estimate hypothetical rewards using an assumed APR, duration, and one-off fee
- **Price stress test:** compare illustrative -50%, -20%, 0%, and +20% price-change scenarios
- **Virtual Portfolio:** record simulated buys, sells, reward credits, and fees; mark positions to manually entered prices; review cash, holdings, equity, and profit/loss
- CSV export of the virtual transaction ledger
- Portable JSON backup and restore for the virtual portfolio
- **Yield Research:** compare buy-and-hold, native staking, centralized lending, DeFi lending, stablecoin yield, and liquidity provision with liquidity notes, qualitative risks, and due-diligence questions; no stale or invented APY claims
- Automated tests for backtesting, paper trading, income scenarios, portfolio accounting, and yield research
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

The example strategy holds the asset when the fast simple moving average (SMA) is above the slow SMA, otherwise it stays in cash. Signals are shifted by one candle so the strategy does not use the same day's closing price to trade at that close. A configurable fee and estimated slippage are applied when the position changes. Strategy and benchmark use the same comparison window after the slow moving average becomes available; comparison dates and candle count are shown.

This is an educational daily-close model, not a production trading engine. It uses a flat slippage estimate rather than a live bid/ask spread; taxes, exchange outages, funding, liquidity constraints, and actual order execution are not modeled. Parameter tuning can overfit historical data.

## Paper Trading

The Paper Trading tab replays the selected SMA signal over historical candles using virtual cash and records simulated buys/sells, equity, drawdown, fees, and estimated slippage. It is a historical simulation, not a forward-running live paper account, and it never submits exchange orders.

## Portfolio backups

Download the virtual portfolio as JSON before ending a session, then upload that file later to restore the ledger. CSV exports are also available. The hosted app deliberately does not store every visitor's portfolio in a shared server database.

## Publish on Streamlit Community Cloud

1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
2. Choose **Create app**, select repository `olgamiran/crypto-radar`, branch `main`, and main file `app.py`.
3. Deploy and wait for the build to finish; Streamlit will provide the app URL.
4. Check the Market & backtest and Paper Trading tabs after deployment.

Deployment must be initiated by the repository owner from their account; it has not been published by this commit. Hosted filesystem storage may be ephemeral, so use portfolio backups. Do not commit API keys or secrets.

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
- [x] Add portable JSON backup and restore for virtual portfolio history
- [ ] Add private durable storage for deployed multi-user use (requires authentication and per-user storage)
- [x] Add Docker packaging for reproducible local runs
- [ ] Publish a demo with Streamlit Community Cloud

## Risks and learning resources

Crypto staking, lending, and yield products can involve market, custody, technical, liquidity, counterparty, and regulatory risks. High advertised rates are not guarantees. Read the Austrian Financial Market Authority's overview before researching real products: [FMA Austria — Which crypto-assets and services are regulated?](https://www.fma.gv.at/en/investments/which-crypto-assets-and-services-are-regulated-and-which-are-not/).

## License

This project is released under the MIT License. See [LICENSE](LICENSE).

## Deploy to Streamlit Community Cloud

1. Push the project to a public GitHub repository.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create a new app and select this repository, the `main` branch, and `app.py` as the entry point.
3. Deploy the app. Later commits pushed to the selected branch normally trigger a redeploy; check the app's **Manage app** logs if startup fails.
4. Open the public app URL and verify each tab after deployment.

The repository includes `.streamlit/config.toml` with basic server defaults. Do not put API keys, passwords, wallet seed phrases, or other secrets into source files or commit them to GitHub.

## Important persistence note

Streamlit session state is temporary. The virtual portfolio is not a cloud database: a session can reset after a browser reconnect, app restart, or redeploy. Export the CSV ledger and download a JSON backup regularly if you want to keep your virtual records. A downloaded backup stays on your own device unless you choose to share it.

Paper Trading replays historical daily candles; it is not a persistent live simulation and does not submit orders. Results depend on the selected date range, SMA windows, fees, and estimated slippage. Treat all outputs as educational experiments rather than forecasts or financial advice.
