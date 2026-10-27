from __future__ import annotations

import pandas as pd
import streamlit as st

from crypto_radar.backtest import run_backtest
from crypto_radar.data import SYMBOLS, fetch_prices
from crypto_radar.income import build_scenarios, calculate_income_scenario

st.set_page_config(page_title="Crypto Radar", page_icon="📡", layout="wide")
st.title("📡 Crypto Radar")
st.caption("Market research, strategy backtesting, and hypothetical crypto-income scenarios. Educational use only; not investment advice.")

with st.sidebar:
    st.header("Market settings")
    label = st.selectbox("Asset", list(SYMBOLS.keys()))
    symbol = SYMBOLS[label]
    period = st.selectbox("History", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    st.divider()
    st.header("Backtest settings")
    fast_window = st.slider("Fast SMA (days)", min_value=2, max_value=100, value=20)
    slow_window = st.slider("Slow SMA (days)", min_value=3, max_value=250, value=50)
    fee_pct = st.number_input("Fee per position change (%)", min_value=0.0, max_value=5.0, value=0.1, step=0.05)

market_tab, income_tab = st.tabs(["📊 Market & backtest", "🧪 Crypto Income Lab"])

with market_tab:
    prices, source_label = fetch_prices(symbol, period)
    st.info(f"Data source: {source_label}. Verify data independently before making decisions.")
    if fast_window >= slow_window:
        st.warning("Fast SMA must be smaller than Slow SMA. Adjust the sliders to run the backtest.")
    else:
        result, metrics = run_backtest(prices, fast_window, slow_window, fee_pct)
        latest = float(prices["Close"].iloc[-1])
        previous = float(prices["Close"].iloc[-2]) if len(prices) > 1 else latest
        change = (latest / previous - 1) * 100 if previous else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Latest close", f"${latest:,.2f}", f"{change:+.2f}% daily")
        c2.metric("Strategy return", f"{metrics['strategy_return']:.2%}")
        c3.metric("Buy & hold return", f"{metrics['buy_hold_return']:.2%}")
        c4.metric("Max drawdown", f"{metrics['max_drawdown']:.2%}")

        st.subheader(f"{label} — daily close")
        st.line_chart(prices[["Close"]], height=300)
        st.subheader("Strategy equity vs. buy and hold")
        st.line_chart(result[["Strategy Equity", "Buy & Hold Equity"]], height=300)
        st.subheader("Moving averages")
        st.line_chart(result[["Close", "Fast SMA", "Slow SMA"]], height=300)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Sharpe ratio (annualized)", f"{metrics['sharpe_ratio']:.2f}")
        m2.metric("Annualized volatility", f"{metrics['annualized_volatility']:.2%}")
        m3.metric("CAGR", f"{metrics['cagr']:.2%}")
        m4.metric("Position changes", f"{int(metrics['trade_count'])}")

        st.subheader("Latest data")
        st.dataframe(result.tail(20).sort_index(ascending=False), use_container_width=True)
        csv = result.to_csv().encode("utf-8")
        st.download_button("Download backtest CSV", data=csv, file_name=f"crypto_radar_{symbol.lower()}_backtest.csv", mime="text/csv")

        with st.expander("How to read this backtest"):
            st.markdown("""
            - The strategy is long-only: it holds the asset when the fast simple moving average is above the slow one.
            - Signals are shifted by one day to reduce look-ahead bias.
            - Fees are a simplified estimate; spread, slippage, taxes, funding, and real execution are not modeled.
            - Historical performance does not predict future results. This app does not place trades or connect to exchange accounts.
            """)

with income_tab:
    st.subheader("Explore hypothetical passive-income scenarios")
    st.write("Estimate how rewards and changes in an asset's price could affect a virtual balance. No wallet or exchange connection is used.")
    with st.form("income_scenario_form"):
        c1, c2 = st.columns(2)
        principal = c1.number_input("Virtual starting balance (USD)", min_value=0.0, max_value=1_000_000_000.0, value=1000.0, step=100.0)
        apr_pct = c2.number_input("Assumed annual reward rate / APR (%)", min_value=0.0, max_value=1000.0, value=5.0, step=0.5)
        c3, c4 = st.columns(2)
        months = c3.slider("Duration (months)", min_value=1, max_value=60, value=12)
        fee_pct_income = c4.number_input("One-off fees (%)", min_value=0.0, max_value=99.0, value=0.0, step=0.1)
        price_change_pct = st.slider("Asset price change over the period (%)", min_value=-100, max_value=100, value=0, step=5)
        submitted = st.form_submit_button("Calculate virtual scenario")

    if submitted:
        scenario = calculate_income_scenario(principal, apr_pct, months, price_change_pct, fee_pct_income)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Hypothetical rewards", f"${scenario['rewards']:,.2f}")
        k2.metric("Ending value", f"${scenario['ending_value']:,.2f}")
        k3.metric("Profit / loss", f"${scenario['profit_loss']:,.2f}", f"{scenario['return_pct']:+.2f}%")
        k4.metric("Assumed fees", f"${scenario['fees']:,.2f}")

        st.subheader("Stress-test: different asset-price paths")
        scenario_rows = build_scenarios(principal, apr_pct, months, fee_pct_income)
        table = pd.DataFrame(scenario_rows)
        table = table[["asset_price_change_pct", "rewards", "fees", "ending_value", "profit_loss", "return_pct"]]
        table.columns = ["Asset price change (%)", "Rewards ($)", "Fees ($)", "Ending value ($)", "Profit / loss ($)", "Return (%)"]
        st.dataframe(table.round(2), use_container_width=True, hide_index=True)
        st.caption("The table assumes price changes of -50%, -20%, 0%, and +20%. These are illustrative scenarios, not forecasts.")

    with st.expander("Assumptions and limitations"):
        st.markdown("""
        - The reward rate is an assumption entered by you, not a live offer or guaranteed rate.
        - Rewards are modeled with monthly compounding at a constant APR.
        - The selected asset-price change applies to the starting balance plus modeled rewards.
        - The one-off fee is deducted from the starting balance. Taxes, lock-up periods, changing rates, liquidity, stablecoin depegs, slashing, hacks, and provider/protocol failure are not modeled.
        - A positive reward rate does not prevent an overall loss if the asset price falls.
        - This calculator is for learning and virtual research only; it does not connect to wallets, stake assets, lend funds, or place trades.
        """)

st.divider()
st.caption("Research tool only — no real funds, wallet connection, staking, lending, or trading. Not financial advice.")
