from __future__ import annotations

import pandas as pd
import streamlit as st

from crypto_radar.backtest import compare_execution_cost_scenarios, compare_sma_parameter_sets, run_backtest, summarize_walk_forward_stability, walk_forward_sma_evaluation
from crypto_radar.data import SYMBOLS, assess_price_data, fetch_prices
from crypto_radar.income import build_scenarios, calculate_income_scenario, compare_income_methods, stress_test_income_methods, validate_income_snapshot, evaluate_income_snapshot
from crypto_radar.portfolio import build_portfolio_snapshot
from crypto_radar.paper_trading import simulate_sma_paper_trades
import json
from crypto_radar.yield_research import get_categories, get_research_methods

st.set_page_config(page_title="Crypto Radar", page_icon="📡", layout="wide")
st.title("📡 Crypto Radar")
st.caption("Market research, strategy backtesting, and hypothetical crypto-income scenarios. Educational use only; not investment advice.")


@st.cache_data(ttl=900, show_spinner=False)
def load_market_prices(symbol: str, period: str):
    """Cache market data briefly so UI interactions do not repeatedly call the provider."""
    return fetch_prices(symbol, period)

with st.sidebar:
    st.header("Market settings")
    label = st.selectbox("Asset", list(SYMBOLS.keys()))
    symbol = SYMBOLS[label]
    period = st.selectbox("History", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    st.divider()
    st.header("Backtest settings")
    period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}[period]
    slow_max = min(250, period_days)
    fast_window = st.slider("Fast SMA (days)", min_value=2, max_value=min(100, slow_max - 1), value=min(20, slow_max - 1))
    slow_window = st.slider("Slow SMA (days)", min_value=3, max_value=slow_max, value=min(50, slow_max))
    fee_pct = st.number_input("Fee per position change (%)", min_value=0.0, max_value=5.0, value=0.1, step=0.05)
    slippage_pct = st.number_input("Estimated slippage per change (%)", min_value=0.0, max_value=5.0, value=0.05, step=0.05)

market_tab, paper_tab, income_tab, portfolio_tab, yield_tab = st.tabs(["📊 Market & backtest", "🧾 Paper Trading", "🧪 Crypto Income Lab", "💼 Virtual Portfolio", "🔎 Yield Research"])

with market_tab:
    prices, source_label = load_market_prices(symbol, period)
    st.info(f"Data source: {source_label}. Verify data independently before making decisions.")
    data_quality = assess_price_data(prices)
    with st.expander("🩺 Market data quality", expanded="DEMO DATA" in source_label or (data_quality["latest_age_days"] is not None and data_quality["latest_age_days"] > 3)):
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Daily bars", f"{data_quality['bars']:,}")
        q2.metric("History starts", str(data_quality["start_date"] or "N/A"))
        q3.metric("Latest candle", str(data_quality["end_date"] or "N/A"))
        q4.metric("Latest age", f"{data_quality['latest_age_days']} day(s)" if data_quality["latest_age_days"] is not None else "N/A")
        st.caption(
            f"Missing calendar days across the series: {data_quality['missing_calendar_days']}. "
            f"Largest gap: {data_quality['max_gap_days']} day(s). "
            f"Duplicate timestamps: {data_quality['duplicate_timestamps']}. "
            f"Invalid close rows: {data_quality['invalid_close_rows']}."
        )
        if "DEMO DATA" in source_label:
            st.warning("These are generated demonstration prices, not actual market history. Do not use them to evaluate a real trading strategy.")
        if data_quality["latest_age_days"] is not None and data_quality["latest_age_days"] > 3 and "DEMO DATA" not in source_label:
            st.warning("The latest available candle is more than three days old. Results may not reflect current market conditions.")
        if data_quality["missing_calendar_days"] > 3:
            st.warning("The price history contains multiple missing calendar days; backtest results may be affected.")
    if fast_window >= slow_window:
        st.warning("Fast SMA must be smaller than Slow SMA. Adjust the sliders to run the backtest.")
    else:
        result, metrics = run_backtest(prices, fast_window, slow_window, fee_pct, slippage_pct)
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
        st.caption(f"Fair comparison window: {metrics['comparison_start']} – {metrics['comparison_end']} ({int(metrics['comparison_bars'])} candles). Costs include fees and estimated slippage.")
        st.metric("Buy & Hold max drawdown", f"{metrics['buy_hold_max_drawdown']:.2%}")

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

        with st.expander("🧾 Execution-cost stress test", expanded=False):
            st.write("Keep the same SMA signals and historical dates, then compare the result if fees and estimated slippage were 1×, 2×, or 4× the sidebar assumptions.")
            try:
                cost_stress = compare_execution_cost_scenarios(
                    prices, fast_window, slow_window, fee_pct=fee_pct, slippage_pct=slippage_pct
                )
                st.dataframe(cost_stress.round(3), use_container_width=True, hide_index=True)
                st.download_button(
                    "Download execution-cost stress test (CSV)",
                    data=cost_stress.to_csv(index=False).encode("utf-8"),
                    file_name=f"execution_cost_stress_{symbol.lower()}.csv",
                    mime="text/csv",
                )
                if cost_stress["Excess vs Buy & Hold (pp)"].iloc[-1] < 0:
                    st.warning("Under the 4× cost assumption, the strategy underperformed Buy & Hold on this historical window.")
                st.caption("Cost multipliers are illustrative, not live exchange quotes. Cumulative cost is the sum of modeled per-change charges, not a full accounting statement. Higher costs can materially change historical results; this is not a forecast.")
            except ValueError as error:
                st.info(f"Cost stress test is not available for this history: {error}")


    st.divider()
    st.subheader("🧪 SMA parameter lab — train vs. test")
    st.write("Compare several moving-average settings on an earlier training period and a later holdout period. The test period is chronological and is not used to choose settings.")
    if len(prices) >= 20:
        max_slow_for_lab = max(5, int(len(prices) * 0.5))
        candidate_configs = [(3, 5), (5, 10), (5, 15), (10, 30), (20, 50), (20, 100), (50, 150)]
        lab_configs = [(fast, slow) for fast, slow in candidate_configs if fast < slow and slow <= max_slow_for_lab]
        if not lab_configs:
            lab_configs = [(2, 3)]
        try:
            comparison = compare_sma_parameter_sets(
                prices, lab_configs, train_fraction=0.7,
                fee_pct=fee_pct, slippage_pct=slippage_pct,
            )
            st.dataframe(comparison.round(2), use_container_width=True, hide_index=True)
            st.download_button(
                "Download SMA parameter comparison (CSV)",
                data=comparison.to_csv(index=False).encode("utf-8"),
                file_name=f"sma_parameter_lab_{symbol.lower()}.csv",
                mime="text/csv",
            )
            st.caption("Sorted by test-period excess return versus Buy & Hold. This is a historical comparison, not a forecast; choosing the top row after looking at test results would introduce selection bias.")
        except ValueError as error:
            st.info(f"Parameter comparison is not available for this history: {error}")
    else:
        st.info("At least 20 valid daily price bars are needed for the parameter lab.")


    st.divider()
    st.subheader("🔁 Walk-forward SMA lab")
    st.write("Choose SMA settings using past candles only, then test them on the next unseen block. Repeat with expanding training history and non-overlapping test blocks.")
    wf_fold_count = st.slider("Walk-forward test periods", min_value=2, max_value=6, value=3, step=1, help="More periods means shorter unseen test blocks. This is not a guarantee of stronger evidence.")
    if len(prices) >= 120:
        wf_candidates = [(3, 5), (5, 10), (5, 15), (10, 30), (20, 50), (20, 100), (50, 150)]
        wf_initial_train = max(90, len(prices) // 2)
        wf_configs = [(fast, slow) for fast, slow in wf_candidates if slow < wf_initial_train]
        try:
            wf_table = walk_forward_sma_evaluation(
                prices, wf_configs, n_folds=wf_fold_count,
                fee_pct=fee_pct, slippage_pct=slippage_pct,
            )
            st.dataframe(wf_table.round(2), use_container_width=True, hide_index=True)

            st.markdown("**Return by unseen test period (%)**")
            wf_chart = wf_table.set_index("Fold")[["Test return (%)", "Test Buy & Hold (%)"]].rename(
                columns={"Test return (%)": "SMA strategy", "Test Buy & Hold (%)": "Buy & Hold"}
            )
            st.bar_chart(wf_chart, x_label="Walk-forward test period", y_label="Return (%)")
            st.markdown("**Strategy advantage by period (percentage points)**")
            st.bar_chart(
                wf_table.set_index("Fold")[["Test excess vs Buy & Hold (pp)"]].rename(
                    columns={"Test excess vs Buy & Hold (pp)": "Strategy minus Buy & Hold"}
                ),
                x_label="Walk-forward test period",
                y_label="Excess return (pp)",
            )
            winning_folds = int((wf_table["Test excess vs Buy & Hold (pp)"] > 0).sum())
            st.caption(
                f"Strategy beat Buy & Hold in {winning_folds} of {len(wf_table)} held-out periods. "
                "A positive bar indicates outperformance, not necessarily a profit."
            )
            wf_return = (1 + wf_table["Test return (%)"] / 100).prod() - 1
            wf_hold = (1 + wf_table["Test Buy & Hold (%)"] / 100).prod() - 1
            w1, w2, w3 = st.columns(3)
            w1.metric("Combined out-of-sample return", f"{wf_return:.2%}")
            w2.metric("Combined Buy & Hold return", f"{wf_hold:.2%}")
            w3.metric("Out-of-sample excess", f"{(wf_return - wf_hold) * 100:+.2f} pp")
            st.markdown("**Strategy stability — descriptive diagnostics**")
            wf_stability, wf_frequency = summarize_walk_forward_stability(wf_table)
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Profitable test periods", f"{wf_stability['profitable_folds']} / {wf_stability['fold_count']}")
            s2.metric("Beat Buy & Hold", f"{wf_stability['outperforming_folds']} / {wf_stability['fold_count']}")
            s3.metric("Worst test return", f"{wf_stability['worst_fold_return_pct']:+.2f}%")
            s4.metric("Return range", f"{wf_stability['return_range_pp']:.2f} pp")
            st.caption(
                f"Best test return: {wf_stability['best_fold_return_pct']:+.2f}%. "
                f"Standard deviation across test-period returns: {wf_stability['return_std_pp']:.2f} pp. "
                "A wide range suggests results differ considerably between periods."
            )
            st.markdown("**How often each SMA pair was selected**")
            wf_frequency = wf_frequency.copy()
            wf_frequency["SMA pair"] = (
                wf_frequency["Selected fast SMA"].astype(str) + " / "
                + wf_frequency["Selected slow SMA"].astype(str)
            )
            st.bar_chart(wf_frequency.set_index("SMA pair")[["Folds selected"]],
                         x_label="Fast / slow SMA", y_label="Test periods selected")
            st.caption(
                f"{wf_stability['distinct_sma_pairs']} different SMA pair(s) were selected. "
                f"These are descriptive statistics from only {wf_fold_count} historical test periods, "
                "not a reliability score, statistical significance test, or future forecast."
            )
            st.download_button(
                "Download SMA selection frequencies (CSV)",
                data=wf_frequency.to_csv(index=False).encode("utf-8"),
                file_name=f"walk_forward_sma_frequency_{symbol.lower()}.csv",
                mime="text/csv",
            )
            st.download_button(
                "Download walk-forward results (CSV)",
                data=wf_table.to_csv(index=False).encode("utf-8"),
                file_name=f"walk_forward_{symbol.lower()}.csv",
                mime="text/csv",
            )
            st.caption(f"{wf_fold_count} chronological, non-overlapping test blocks. Each fold selects the highest net training return using only earlier candles; signals have a one-bar lag. Results include estimated costs. Repeatedly changing candidates after seeing these results can still overfit.")
            if "DEMO DATA" in source_label:
                st.warning("Walk-forward results use demonstration prices, not actual market history.")
        except ValueError as error:
            st.info(f"Walk-forward lab is not available: {error}")
    else:
        st.info("Choose a longer history (at least 120 valid daily bars) to run walk-forward testing.")


    st.divider()
    with st.expander("🌍 Compare walk-forward results across crypto assets", expanded=False):
        st.write("Apply the same history length, SMA candidate rules, number of test periods, fees and slippage to selected assets. Each asset chooses SMA settings from its own past.")
        comparison_assets = st.multiselect(
            "Assets to compare", options=list(SYMBOLS.keys()),
            default=list(SYMBOLS.keys())[:3],
            key="wf_compare_assets",
        )
        if st.button("Run cross-asset comparison", key="run_wf_asset_comparison"):
            asset_rows = []
            for asset_name in comparison_assets:
                asset_symbol = SYMBOLS[asset_name]
                asset_prices, asset_source = load_market_prices(asset_symbol, period)
                valid_count = len(asset_prices[["Close"]].dropna())
                asset_initial_train = max(90, valid_count // 2)
                asset_configs = [
                    (fast, slow) for fast, slow in
                    [(3, 5), (5, 10), (5, 15), (10, 30), (20, 50), (20, 100), (50, 150)]
                    if slow < asset_initial_train
                ]
                try:
                    asset_folds = walk_forward_sma_evaluation(
                        asset_prices, asset_configs, n_folds=wf_fold_count,
                        fee_pct=fee_pct, slippage_pct=slippage_pct,
                    )
                    asset_stability, _ = summarize_walk_forward_stability(asset_folds)
                    asset_strategy = (1 + asset_folds["Test return (%)"] / 100).prod() - 1
                    asset_hold = (1 + asset_folds["Test Buy & Hold (%)"] / 100).prod() - 1
                    asset_rows.append({
                        "Asset": asset_name,
                        "Data source": "DEMO" if "DEMO DATA" in asset_source else "Yahoo Finance",
                        "Test start": asset_folds["Test start"].iloc[0],
                        "Test end": asset_folds["Test end"].iloc[-1],
                        "Out-of-sample return (%)": asset_strategy * 100,
                        "Buy & Hold (%)": asset_hold * 100,
                        "Excess return (pp)": (asset_strategy - asset_hold) * 100,
                        "Profitable periods": asset_stability["profitable_folds"],
                        "Periods beating Buy & Hold": asset_stability["outperforming_folds"],
                        "Test periods": wf_fold_count,
                    })
                except ValueError as error:
                    st.info(f"{asset_name}: unavailable — {error}")
            if asset_rows:
                asset_comparison = pd.DataFrame(asset_rows)
                st.dataframe(asset_comparison.round(2), hide_index=True, use_container_width=True)
                st.download_button(
                    "Download cross-asset comparison (CSV)",
                    data=asset_comparison.to_csv(index=False).encode("utf-8"),
                    file_name="walk_forward_asset_comparison.csv",
                    mime="text/csv",
                )
                if (asset_comparison["Data source"] == "DEMO").any():
                    st.warning("One or more assets use generated DEMO prices. Do not treat those rows as real market evidence.")
                if asset_comparison["Test start"].nunique() > 1 or asset_comparison["Test end"].nunique() > 1:
                    st.warning("Assets have different test date ranges. Compare returns cautiously; identical history selections do not guarantee identical dates.")
                st.caption("Results are historical, not forecasts. Each asset is independently fitted using past prices; the table is not a portfolio backtest.")
            elif not comparison_assets:
                st.info("Select at least one asset to compare.")

with paper_tab:
    st.subheader("Signal-driven Paper Trading")
    st.write("Simulate historical SMA signals with virtual cash. This does not place orders or connect to an exchange.")
    paper_cash = st.number_input("Paper trading starting cash (USD)", min_value=0.0, max_value=1_000_000_000.0, value=10000.0, step=500.0, key="paper_starting_cash")
    if fast_window >= slow_window:
        st.warning("Set Fast SMA below Slow SMA in the sidebar.")
    else:
        paper_equity, paper_trades, paper_metrics = simulate_sma_paper_trades(prices, fast_window, slow_window, paper_cash, fee_pct, slippage_pct)
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("Final virtual equity", f"${paper_metrics['final_equity']:,.2f}")
        pc2.metric("Profit / loss", f"${paper_metrics['profit_loss']:,.2f}", f"{paper_metrics['return_pct']:+.2f}%")
        pc3.metric("Max drawdown", f"{paper_metrics['max_drawdown']:.2%}")
        pc4.metric("Simulated trades", f"{int(paper_metrics['trade_count'])}")
        b1, b2, b3 = st.columns(3)
        b1.metric("Buy & Hold final value", f"${paper_metrics['buy_hold_final_equity']:,.2f}")
        b2.metric("Buy & Hold return", f"{paper_metrics['buy_hold_return_pct']:+.2f}%")
        b3.metric("Strategy vs. Buy & Hold", f"{paper_metrics['excess_return_pct']:+.2f} pp",
                  help="Difference between strategy return and buy-and-hold return, in percentage points.")
        st.subheader("Virtual strategy vs. buy and hold")
        st.line_chart(paper_equity[["Equity", "Buy & Hold Equity"]], height=300)
        st.caption(f"Buy & Hold maximum drawdown: {paper_metrics['buy_hold_max_drawdown']:.2%}. Both curves start with the same virtual cash and use the same selected history.")
        st.subheader("Simulated trade journal")
        st.dataframe(paper_trades, use_container_width=True, hide_index=True)
        st.download_button("Download paper-trading journal (CSV)", data=paper_trades.to_csv(index=False).encode("utf-8"), file_name=f"paper_trades_{symbol.lower()}.csv", mime="text/csv")
        st.download_button("Download paper equity curve (CSV)", data=paper_equity.to_csv().encode("utf-8"), file_name=f"paper_equity_{symbol.lower()}.csv", mime="text/csv")
        st.caption("Historical simulation is not a live forward-looking paper account. Execution is approximated from daily closes.")

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

    st.divider()
    st.subheader("🧭 Compare virtual crypto-income methods")
    st.write("Compare hypothetical outcomes using your own APR and fee assumptions. These values are not live yields, offers, or recommendations.")
    method_catalog = {
        "Buy and hold": "hold",
        "Native staking": "native-staking",
        "Centralized lending": "centralized-lending",
        "DeFi lending": "defi-lending",
        "Stablecoin yield": "stablecoin-yield",
    }
    research_by_id = {method["id"]: method for method in get_research_methods()}
    with st.form("income_method_comparison"):
        virtual_amount = st.number_input("Comparison balance (virtual USD)", min_value=1.0, max_value=1_000_000_000.0, value=1000.0, step=100.0, key="comparison_amount")
        comparison_months = st.slider("Comparison duration (months)", 1, 60, 12, key="comparison_months")
        volatile_change = st.slider("Volatile-asset price change (%)", -100, 100, 0, step=5, key="comparison_volatile_change")
        stable_change = st.slider("Stablecoin price change / depeg scenario (%)", -100, 20, 0, step=5, key="comparison_stable_change")
        selected_methods = st.multiselect("Methods", list(method_catalog), default=list(method_catalog), key="comparison_methods")
        st.caption("Enter illustrative APR and one-off fees for each method. Zero APR is the buy-and-hold baseline.")
        method_assumptions = []
        for method_name in selected_methods:
            if method_name == "Buy and hold":
                assumed_apr = 0.0
                st.write("**Buy and hold** — 0% yield by definition")
            else:
                assumed_apr = st.number_input(
                    f"{method_name}: assumed APR (%)", 0.0, 1000.0, 0.0,
                    step=0.5, key=f"compare_apr_{method_catalog[method_name]}"
                )
            assumed_fee = st.number_input(
                f"{method_name}: one-off fee (%)", 0.0, 99.0, 0.0,
                step=0.1, key=f"compare_fee_{method_catalog[method_name]}"
            )
            method_assumptions.append({
                "method": method_name,
                "apr_pct": assumed_apr,
                "fee_pct": assumed_fee,
                "price_change_pct": stable_change if method_name == "Stablecoin yield" else volatile_change,
            })
        compare_submitted = st.form_submit_button("Compare virtual methods")
    if compare_submitted:
        if not method_assumptions:
            st.info("Select at least one method.")
        else:
            comparison_rows = compare_income_methods(
                virtual_amount, comparison_months, volatile_change, method_assumptions
            )
            st.session_state["income_latest_snapshot"] = {"version": 1, "name": "Method comparison", "kind": "comparison", "inputs": {"principal": virtual_amount, "months": comparison_months, "methods": method_assumptions}}
            comparison_table = pd.DataFrame(comparison_rows)
            st.dataframe(comparison_table.round(2), use_container_width=True, hide_index=True)
            st.bar_chart(
                comparison_table.set_index("Method")[["Virtual ending value ($)"]],
                x_label="Method", y_label="Hypothetical ending value (USD)"
            )
            st.download_button(
                "Download virtual method comparison (CSV)",
                data=comparison_table.to_csv(index=False).encode("utf-8"),
                file_name="virtual_crypto_income_methods.csv",
                mime="text/csv",
            )
            st.markdown("**Risk and withdrawal considerations (qualitative)**")
            for method_name in selected_methods:
                details = research_by_id[method_catalog[method_name]]
                with st.expander(method_name):
                    st.write(f"**How rewards arise:** {details['reward_source']}")
                    st.write(f"**Liquidity:** {details['liquidity']}")
                    st.write(f"**Main risks:** {details['key_risks']}")
                    st.write(f"**What to verify:** {details['what_to_verify']}")
            st.warning(
                "The chart is NOT risk-adjusted. It excludes defaults, slashing, smart-contract exploits, "
                "withdrawal freezes, taxes and changing reward rates. Stablecoins can depeg. "
                "A larger hypothetical ending value does not mean a safer or better investment."
            )

    st.divider()
    st.subheader("🛡️ Passive-income risk stress test")
    st.write("Explore independent hypothetical shocks and a combined worst-case illustration. This does not assign probabilities to any event.")
    with st.form("income_risk_stress"):
        stress_principal = st.number_input("Stress-test virtual balance (USD)", 1.0, 1_000_000_000.0, 1000.0, step=100.0)
        stress_months = st.slider("Stress-test duration (months)", 1, 60, 12)
        stress_method = st.selectbox("Method to stress-test", list(method_catalog))
        stress_apr = st.number_input("Assumed APR (%)", 0.0, 1000.0, 0.0, step=0.5,
                                     disabled=stress_method == "Buy and hold")
        stress_fee = st.number_input("Assumed one-off fee (%)", 0.0, 99.0, 0.0, step=0.1)
        stress_price = st.slider("Baseline asset price change (%)", -100, 100, 0, step=5)
        stress_apr_cut = st.slider("APR reduction (%)", 0, 100, 50, step=5)
        stress_price_shock = st.slider("Additional price decline (percentage points)", -100, 0, -30, step=5)
        stress_haircut = st.slider("Capital loss / unrecovered balance (%)", 0, 100, 25, step=5)
        stress_submitted = st.form_submit_button("Run virtual stress test")
    if stress_submitted:
        stress_rows = stress_test_income_methods(
            stress_principal, stress_months,
            [{
                "method": stress_method,
                "apr_pct": 0.0 if stress_method == "Buy and hold" else stress_apr,
                "fee_pct": stress_fee,
                "price_change_pct": stress_price,
            }],
            apr_cut_pct=stress_apr_cut,
            price_shock_pct=stress_price_shock,
            loss_haircut_pct=stress_haircut,
        )
        st.session_state["income_latest_snapshot"] = {"version": 1, "name": "Risk stress test", "kind": "stress", "inputs": {"principal": stress_principal, "months": stress_months, "methods": [{"method": stress_method, "apr_pct": 0.0 if stress_method == "Buy and hold" else stress_apr, "fee_pct": stress_fee, "price_change_pct": stress_price}], "apr_cut_pct": stress_apr_cut, "price_shock_pct": stress_price_shock, "loss_haircut_pct": stress_haircut}}
        stress_table = pd.DataFrame(stress_rows)
        st.dataframe(stress_table.round(2), use_container_width=True, hide_index=True)
        st.bar_chart(
            stress_table.set_index("Scenario")[["Virtual ending value ($)"]],
            x_label="Hypothetical shock", y_label="Virtual ending value (USD)"
        )
        st.download_button(
            "Download passive-income stress test (CSV)",
            data=stress_table.to_csv(index=False).encode("utf-8"),
            file_name="virtual_income_risk_stress.csv",
            mime="text/csv",
        )
        st.caption(
            "APR reduction lowers the assumed rate for the entire period. The price decline "
            "is added to the baseline price change and capped at -100%. The capital-loss haircut "
            "reduces the modeled final recoverable value after fees and price changes. "
            "Combined shocks apply all three; this is not a statistically estimated worst case."
        )
        st.warning(
            "Capital-loss percentages are illustrative, not default probabilities. "
            "Real-world losses, depegs, frozen withdrawals, and insolvency may behave differently. "
            "The model does not forecast returns or evaluate specific providers."
        )

    st.divider()
    st.subheader("💾 Saved virtual research scenarios")
    st.write("Save comparison or stress-test assumptions for this browser session, or download a JSON backup to restore later. No accounts, wallets or real assets are stored.")
    if "income_saved_snapshots" not in st.session_state:
        st.session_state["income_saved_snapshots"] = []
    latest_snapshot = st.session_state.get("income_latest_snapshot")
    if latest_snapshot:
        snapshot_name = st.text_input("Name your latest scenario", value=latest_snapshot["name"], max_chars=80, key="income_snapshot_name")
        if st.button("Save latest scenario", key="income_save_snapshot"):
            try:
                candidate = validate_income_snapshot({**latest_snapshot, "name": snapshot_name})
                if len(st.session_state["income_saved_snapshots"]) >= 30:
                    st.warning("Maximum 30 saved scenarios per session. Remove one before saving.")
                else:
                    st.session_state["income_saved_snapshots"].append(candidate)
                    st.success("Saved for this browser session. Download JSON to keep it after the session ends.")
            except ValueError as error:
                st.error(str(error))
    uploaded_income = st.file_uploader("Restore a scenario JSON file", type=["json"], key="income_snapshot_upload")
    if uploaded_income is not None and st.button("Import saved scenario", key="income_import_snapshot"):
        try:
            if uploaded_income.size > 100_000:
                raise ValueError("JSON file is too large (maximum 100 KB).")
            restored = validate_income_snapshot(json.loads(uploaded_income.getvalue().decode("utf-8")))
            if len(st.session_state["income_saved_snapshots"]) >= 30:
                raise ValueError("Maximum 30 saved scenarios per session.")
            st.session_state["income_saved_snapshots"].append(restored)
            st.success("Scenario imported. Select it below to recalculate.")
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
            st.error(f"Cannot import scenario: {error}")
    saved_snapshots = st.session_state["income_saved_snapshots"]
    if saved_snapshots:
        selected_index = st.selectbox(
            "Saved scenarios", range(len(saved_snapshots)),
            format_func=lambda i: f"{i + 1}. {saved_snapshots[i]['name']} ({saved_snapshots[i]['kind']})",
            key="income_selected_snapshot",
        )
        selected_snapshot = saved_snapshots[selected_index]
        st.download_button(
            "Download selected scenario (JSON)",
            data=json.dumps(selected_snapshot, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="crypto_radar_income_scenario.json",
            mime="application/json",
        )
        if st.button("Recalculate saved scenario", key="income_replay_snapshot"):
            try:
                replay_table = pd.DataFrame(evaluate_income_snapshot(selected_snapshot))
                st.dataframe(replay_table.round(2), use_container_width=True, hide_index=True)
                st.bar_chart(replay_table.set_index(
                    "Scenario" if selected_snapshot["kind"] == "stress" else "Method"
                )[["Virtual ending value ($)"]])
            except ValueError as error:
                st.error(f"Cannot recalculate scenario: {error}")
        if st.button("Remove selected scenario", key="income_delete_snapshot"):
            saved_snapshots.pop(selected_index)
            st.rerun()
    else:
        st.caption("No saved scenarios yet. Run a method comparison or risk stress test first.")
    st.caption("Session storage is temporary. Download JSON for durable local backup; imported values are validated and results are recalculated.")

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
    if "portfolio_pending_restore" in st.session_state:
        pending = st.session_state.pop("portfolio_pending_restore")
        st.session_state["portfolio_transactions"] = pending["transactions"]
        st.session_state["portfolio_starting_cash"] = pending["starting_cash"]

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
    st.caption("Keep your ledger between sessions with a private JSON backup. The hosted demo does not store user ledgers in a shared server database.")
    backup = json.dumps({"starting_cash": starting_cash, "transactions": transactions}, indent=2)
    st.download_button("Download portfolio backup (JSON)", data=backup, file_name="crypto_radar_portfolio_backup.json", mime="application/json")
    uploaded_backup = st.file_uploader("Restore portfolio backup (JSON)", type=["json"], key="portfolio_backup_upload")
    if uploaded_backup is not None and st.button("Restore uploaded backup"):
        try:
            restored = json.load(uploaded_backup)
            restored_cash = float(restored["starting_cash"])
            restored_transactions = restored["transactions"]
            build_portfolio_snapshot(restored_cash, restored_transactions)
            st.session_state["portfolio_pending_restore"] = {"starting_cash": restored_cash, "transactions": restored_transactions}
            st.success("Backup validated. Applying restored portfolio...")
            st.rerun()
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            st.error(f"Could not restore backup: {error}")

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

    with st.expander("Where to verify current rates and protocol terms"):
        st.markdown("""
        - [DeFiLlama Yields](https://defillama.com/yields) — compare DeFi pool rates; inspect chain, pool composition, liquidity, and methodology.
        - [Ethereum staking documentation](https://ethereum.org/en/staking/) — primary-source overview of native ETH staking mechanics and risks.
        - [Solana staking documentation](https://solana.com/staking) — primary-source overview of SOL staking.
        - [Aave documentation](https://docs.aave.com/) — primary protocol documentation for lending markets and risk parameters.
        - [Uniswap documentation](https://docs.uniswap.org/) — primary protocol documentation for liquidity pools and impermanent-loss considerations.

        Rates are intentionally not copied into this app: providers can change them and APY figures are not directly comparable. When evaluating a rate, record the source URL, observation date/time, chain, exact pool/product, token pair, lock-up, fees, and whether incentives are included.
        """)

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
