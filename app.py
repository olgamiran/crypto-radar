from __future__ import annotations

import streamlit as st

from crypto_radar.backtest import run_backtest
from crypto_radar.data import SYMBOLS, fetch_prices

st.set_page_config(page_title="Crypto Radar", page_icon="📡", layout="wide")
st.title("📡 Crypto Radar")
st.caption("Crypto market dashboard + moving-average strategy lab. Educational use only; not investment advice.")

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

prices, source_label = fetch_prices(symbol, period)
st.info(f"Data source: {source_label}. Verify data independently before making decisions.")
if fast_window >= slow_window:
    st.warning("Fast SMA must be smaller than Slow SMA. Adjust the sliders to run the backtest.")
    st.stop()

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
