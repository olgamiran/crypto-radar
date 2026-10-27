# Changelog

Notable project changes are recorded here.

## 0.2.0 — 2026-10-27

- Added a virtual portfolio ledger for simulated buys, sells, reward credits, and fees.
- Added manual mark-to-market valuation, portfolio P/L, and CSV transaction export.
- Added validation for insufficient virtual cash and overselling.
- Added a yield research catalogue covering holding, staking, centralized lending, DeFi lending, stablecoin yield, and liquidity provision.
- Added risk descriptions and due-diligence questions without presenting unverified APY figures.
- Added finite-number validation for portfolio calculations.
- Cached market data for 15 minutes to reduce repeated provider requests during dashboard interactions.
- Added GitHub Actions checks for Python compilation and all pytest tests.
- Added an MIT license and Docker packaging files.

## 0.1.0 — Initial MVP

- Added Streamlit market dashboard for BTC, ETH, SOL, XRP, and DOGE.
- Added a simple moving-average crossover backtest and performance metrics.
- Added a hypothetical crypto-income calculator with illustrative price stress scenarios.
- Added CSV export and initial automated tests.
