"""Opening hours volatility scanner tab."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from engine.data.storage import DataStore
from engine.execution.paper_trader import AlpacaPaperTrader
from engine.signals.opening_scanner import scan_universe
from engine.signals.ml_ranker import load_ranker_if_available
from engine.signals.regime_filter import RegimeFilter


DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "AMD",
    "NFLX", "COIN", "PLTR", "SOFI", "RIVN", "LCID", "GME", "AMC",
]


def render_opening_scanner_tab() -> None:
    """Render the opening volatility scanner UI."""
    st.markdown(
        """
        <div class="scanner-header">
            <h3>Opening Volatility Scanner</h3>
            <p>Rank tickers by gap, premarket volume, opening range expansion, and relative volume at open.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        tickers_raw = st.text_input(
            "Tickers (comma-separated)",
            value=", ".join(DEFAULT_TICKERS[:12]),
        )
    with col2:
        min_score = st.slider("Min score", 0, 80, 20)
    with col3:
        use_regime = st.checkbox("Regime filter", value=True)
    with col4:
        ranker = load_ranker_if_available()
        use_ml_rank = st.checkbox(
            "ML re-rank",
            value=bool(ranker),
            disabled=ranker is None,
            help="Requires a trained model at data/models/opening_ranker.joblib",
        )

    if st.button("Run Opening Scan", type="primary", use_container_width=True):
        tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
        if not tickers:
            st.warning("Enter at least one ticker.")
            return

        with st.spinner(f"Scanning {len(tickers)} tickers..."):
            regime_filter = RegimeFilter() if use_regime else None
            results = scan_universe(tickers, regime_filter=regime_filter, min_score=min_score)

        if results.empty:
            st.info("No tickers met the minimum score threshold.")
            return

        if use_ml_rank and ranker is not None:
            results = ranker.rank(results)

        st.session_state["opening_scan_results"] = results

        # Persist top signals
        try:
            store = DataStore()
            for _, row in results.head(10).iterrows():
                store.log_signal(
                    row["ticker"],
                    "opening_scan",
                    row.get("opening_score"),
                    row.to_dict(),
                )
        except Exception:
            pass

    if "opening_scan_results" in st.session_state:
        df = st.session_state["opening_scan_results"]
        display_cols = [
            c
            for c in [
                "ticker",
                "opening_score",
                "ml_score",
                "direction",
                "price",
                "gap_pct",
                "premarket_volume_ratio",
                "or_15m_range_pct",
                "relative_volume_open",
                "regime_label",
                "volatility",
            ]
            if c in df.columns
        ]
        st.dataframe(
            _format_scanner_df(df[display_cols]),
            use_container_width=True,
            hide_index=True,
        )

        if len(df) > 0:
            top = df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Top pick", top["ticker"])
            c2.metric("Score", f"{top['opening_score']:.0f}")
            c3.metric("Gap", f"{top.get('gap_pct', 0):+.2f}%")
            c4.metric("Regime", top.get("regime_label", "—"))

        _render_paper_trading_panel(df)


def _render_paper_trading_panel(results: pd.DataFrame) -> None:
    """Optional Alpaca paper execution — requires explicit user confirmation."""
    with st.expander("Paper Trading (Alpaca)", expanded=False):
        st.caption(
            "Submit market orders on your Alpaca paper account for the top ranked "
            "signals. Orders are not placed until you confirm below."
        )

        trader_probe = AlpacaPaperTrader()
        alpaca_ready = trader_probe.configured

        if alpaca_ready:
            st.success("Alpaca credentials detected.")
        else:
            st.info(
                "No Alpaca credentials found — enable dry run to preview orders, "
                "or set ALPACA_API_KEY and ALPACA_SECRET_KEY in your environment."
            )

        c1, c2, c3 = st.columns(3)
        with c1:
            max_orders = st.number_input("Max orders", min_value=1, max_value=5, value=3)
        with c2:
            notional_usd = st.number_input(
                "Notional per trade ($)", min_value=100, max_value=5000, value=500, step=100
            )
        with c3:
            trade_min_score = st.slider("Min score to trade", 0, 100, 50)

        dry_run = st.checkbox(
            "Dry run (simulate orders, do not submit)",
            value=not alpaca_ready,
            disabled=not alpaca_ready,
            help="When Alpaca is not configured, dry run is always used.",
        )
        if not alpaca_ready:
            dry_run = True

        if alpaca_ready and not dry_run:
            try:
                account = trader_probe.get_account()
                st.metric("Buying power", f"${float(account.get('buying_power', 0)):,.0f}")
            except Exception as exc:
                st.error(f"Could not load Alpaca account: {exc}")

        confirm = st.checkbox(
            "I confirm I want to submit paper market orders for the top ranked signals",
            value=False,
        )

        if st.button(
            "Execute Top Signals",
            type="secondary",
            disabled=not confirm,
            use_container_width=True,
        ):
            trader = AlpacaPaperTrader(dry_run=dry_run)
            signals = results.to_dict(orient="records")
            try:
                with st.spinner("Submitting orders..."):
                    placed = trader.execute_top_signals(
                        signals,
                        max_orders=int(max_orders),
                        notional_usd=float(notional_usd),
                        min_score=float(trade_min_score),
                    )
            except Exception as exc:
                st.error(f"Order submission failed: {exc}")
                return

            if not placed:
                st.warning("No signals met the trade minimum score or notional threshold.")
                return

            st.session_state["opening_paper_orders"] = placed
            mode = "simulated" if dry_run else "submitted"
            st.success(f"{len(placed)} order(s) {mode}.")

        if "opening_paper_orders" in st.session_state:
            rows = []
            for item in st.session_state["opening_paper_orders"]:
                signal = item["signal"]
                order = item["order"]
                rows.append(
                    {
                        "ticker": signal.get("ticker"),
                        "score": signal.get("opening_score"),
                        "side": order.get("side"),
                        "qty": order.get("qty"),
                        "status": order.get("status"),
                        "order_id": order.get("id"),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _format_scanner_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "price" in out.columns:
        out["price"] = out["price"].map(lambda x: f"${x:.2f}")
    if "gap_pct" in out.columns:
        out["gap_pct"] = out["gap_pct"].map(lambda x: f"{x:+.2f}%")
    if "opening_score" in out.columns:
        out["opening_score"] = out["opening_score"].map(lambda x: f"{x:.0f}")
    if "ml_score" in out.columns:
        out["ml_score"] = out["ml_score"].map(lambda x: f"{x:.0f}")
    if "volatility" in out.columns:
        out["volatility"] = out["volatility"].map(lambda x: f"{x:.1%}")
    if "premarket_volume_ratio" in out.columns:
        out["premarket_volume_ratio"] = out["premarket_volume_ratio"].map(lambda x: f"{x:.2f}x")
    if "relative_volume_open" in out.columns:
        out["relative_volume_open"] = out["relative_volume_open"].map(lambda x: f"{x:.2f}x")
    if "or_15m_range_pct" in out.columns:
        out["or_15m_range_pct"] = out["or_15m_range_pct"].map(lambda x: f"{x:.2f}%")
    return out
