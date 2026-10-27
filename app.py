from __future__ import annotations

import pandas as pd
import streamlit as st

from crypto_radar.backtest import run_backtest
from crypto_radar.data import SYMBOLS, fetch_prices
from crypto_radar.income import build_scenarios, calculate_income_scenario
from crypto_radar.portfolio import build_portfolio_snapshot
from crypto_radar.yield_research import get_categories, get_research_methods

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

market_tab, income_tab, portfolio_tab, yield_tab = st.tabs(["📊 Market & backtest", "🧪 Crypto Income Lab", "💼 Virtual Portfolio", "🔎 Yield Research"])

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


with portfolio_tab:
    st.subheader("Virtual Portfolio")
    st.write("Track simulated buys, sells, reward credits, and fees. This ledger lives in the current app session; it does not connect to an exchange or wallet.")
    st.caption("All asset prices in this tab are manually entered hypothetical prices, not live market quotes.")

    if "portfolio_transactions" not in st.session_state:
        st.session_state["portfolio_transactions"] = []
    if "portfolio_starting_cash" not in st.session_state:
        st.session_state["portfolio_starting_cash"] = 10000.0

    starting_cash = st.number_input(
        "Starting virtual cash (USD)",
        min_value=0.0,
        max_value=1_000_000_000.0,
        step=500.0,
        disabled=bool(st.session_state["portfolio_transactions"]),
        key="portfolio_starting_cash",
        help="Locked after the first ledger entry so historical accounting stays consistent.",
    )
    transactions = st.session_state["portfolio_transactions"]

    try:
        base_snapshot = build_portfolio_snapshot(starting_cash, transactions)
        held_assets = [
            str(row["asset"])
            for _, row in base_snapshot["positions"].iterrows()
        ]
        current_prices = {}
        if held_assets:
            st.markdown("**Mark-to-market prices**")
            st.caption("Enter a hypothetical current price for each held asset. The last transaction price is the initial reference, not a live quote.")
            price_cols = st.columns(min(3, len(held_assets)))
            for index, asset in enumerate(held_assets):
                last_price = float(base_snapshot["positions"].loc[base_snapshot["positions"]["asset"] == asset, "price_usd"].iloc[0])
                with price_cols[index % len(price_cols)]:
                    mark_key = f"portfolio_mark_{asset}"
                    if mark_key not in st.session_state:
                        st.session_state[mark_key] = last_price
                    current_prices[asset] = st.number_input(
                        f"{asset} price (USD)",
                        min_value=0.0,
                        max_value=1_000_000_000.0,
                        step=max(last_price * 0.01, 0.01),
                        key=mark_key,
                    )
        snapshot = build_portfolio_snapshot(starting_cash, transactions, current_prices)

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Portfolio value", f"${snapshot['equity']:,.2f}")
        p2.metric("Virtual cash", f"${snapshot['cash']:,.2f}")
        p3.metric("Profit / loss", f"${snapshot['profit_loss']:,.2f}", f"{snapshot['return_pct']:+.2f}%")
        p4.metric("Recorded fees", f"${snapshot['total_fees']:,.2f}")

        st.subheader("Current positions")
        if snapshot["positions"].empty:
            st.info("Your virtual portfolio is empty. Add a simulated purchase or reward below to get started.")
        else:
            position_view = snapshot["positions"].copy()
            position_view.columns = ["Asset", "Quantity", "Mark price ($)", "Market value ($)"]
            st.dataframe(position_view.round(6), use_container_width=True, hide_index=True)

        st.subheader("Add a virtual transaction")
        with st.form("portfolio_transaction_form", clear_on_submit=True):
            tx_type = st.selectbox("Transaction type", ["BUY", "SELL", "REWARD", "FEE"])
            asset = st.selectbox("Asset", list(SYMBOLS.values()))
            if tx_type == "FEE":
                quantity = 0.0
                price_usd = 0.0
                st.caption("A fee-only entry records an expense in virtual cash.")
            else:
                quantity = st.number_input("Quantity (coins)", min_value=0.00000001, max_value=1_000_000_000.0, value=0.01, format="%.8f")
                price_usd = st.number_input("Transaction price per coin (USD)", min_value=0.0, max_value=1_000_000_000.0, value=100.0, step=10.0)
            fee_usd = st.number_input("Fee (USD)", min_value=0.0, max_value=1_000_000_000.0, value=0.0, step=0.1)
            tx_date = st.date_input("Transaction date")
            add_tx = st.form_submit_button("Add virtual transaction")

        if add_tx:
            candidate = {
                "date": tx_date.isoformat(),
                "type": tx_type,
                "asset": "" if tx_type == "FEE" else asset,
                "quantity": quantity,
                "price_usd": price_usd,
                "fee_usd": fee_usd,
            }
            try:
                build_portfolio_snapshot(starting_cash, transactions + [candidate], current_prices)
            except ValueError as error:
                st.error(str(error))
            else:
                st.session_state["portfolio_transactions"].append(candidate)
                st.rerun()

        st.subheader("Transaction history")
        if snapshot["ledger"].empty:
            st.caption("No transactions recorded yet.")
        else:
            ledger_view = snapshot["ledger"].copy()
            ledger_view.columns = [
                "Date", "Type", "Asset", "Quantity", "Transaction price ($)",
                "Gross value ($)", "Fee ($)", "Cash after ($)", "Units after",
            ]
            st.dataframe(ledger_view.round(6), use_container_width=True, hide_index=True)
            st.download_button(
                "Download transaction history (CSV)",
                data=snapshot["ledger"].to_csv(index=False).encode("utf-8"),
                file_name="crypto_radar_virtual_portfolio.csv",
                mime="text/csv",
            )

        if transactions and st.button("Reset virtual portfolio", type="secondary"):
            st.session_state["portfolio_transactions"] = []
            st.rerun()

        with st.expander("Accounting rules and limitations"):
            st.markdown("""
            - BUY decreases virtual cash by quantity × transaction price plus fees.
            - SELL increases cash by quantity × transaction price minus fees and cannot exceed held units.
            - REWARD adds units to holdings; it does not add cash. Its value depends on the entered mark price.
            - FEE records a standalone virtual cash expense.
            - Current valuation uses your manually entered mark prices, defaulting to the last transaction price.
            - The ledger is stored in Streamlit session state and may reset when the session ends or the app restarts.
            - This is a simplified educational ledger, not tax accounting, a broker statement, or investment advice.
            """)

    except ValueError as error:
        st.error(f"Portfolio cannot be calculated: {error}")
        st.info("Reset the virtual portfolio or review the entries to restore a valid ledger.")


with yield_tab:
    st.subheader("Crypto Yield Research")
    st.write("Compare common ways people seek crypto-related returns. This is a general risk-research catalogue, not a list of live offers or a recommendation.")
    st.warning("No live APY values are shown. Advertised rates can change quickly and do not guarantee a positive total return.")

    category = st.selectbox("Filter by mechanism", get_categories(), key="yield_category_filter")
    methods = get_research_methods(category)
    summary = pd.DataFrame([
        {
            "Method": item["name"],
            "Category": item["category"],
            "Potential reward source": item["reward_source"],
            "Liquidity considerations": item["liquidity"],
            "General risk level": item["risk_level"],
        }
        for item in methods
    ])
    st.dataframe(summary, use_container_width=True, hide_index=True)

    if methods:
        selected_id = st.selectbox(
            "Explore risks and due-diligence questions",
            options=[item["id"] for item in methods],
            format_func=lambda method_id: next(item["name"] for item in methods if item["id"] == method_id),
            key="yield_method_detail",
        )
        selected = next(item for item in methods if item["id"] == selected_id)
        st.markdown(f"### {selected['name']}")
        st.markdown(f"**How returns may be generated:** {selected['reward_source']}")
        st.markdown(f"**Liquidity:** {selected['liquidity']}")
        st.markdown(f"**General risk level:** {selected['risk_level']}")
        st.markdown(f"**Key risks:** {selected['key_risks']}")
        st.markdown(f"**Questions to verify:** {selected['what_to_verify']}")

    with st.expander("Due-diligence checklist before considering any real product"):
        st.markdown("""
        - Identify exactly where the return comes from; do not rely on a headline APY.
        - Read withdrawal, lock-up, redemption, and fee terms.
        - Research custody, counterparty, smart-contract, oracle, and governance risks as applicable.
        - Check whether incentives are temporary and whether the underlying asset can lose value.
        - Consider what happens during a market crash, a stablecoin depeg, a platform outage, or a hack.
        - Confirm the provider's legal entity and the applicable regulatory protections in your jurisdiction.
        - Never treat this educational catalogue as a product endorsement or guaranteed-return list.
        """)

st.divider()
st.caption("Research tool only — no real funds, wallet connection, staking, lending, or trading. Not financial advice.")
