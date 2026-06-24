"""Signal performance dashboard tab."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from engine.analytics.signal_history import build_equity_curve, compute_hit_rates, parse_signal_history
from engine.data.storage import DataStore


def render_performance_dashboard() -> None:
    """Render signal history, equity curve, and performance metrics."""
    st.markdown(
        """
        <div class="scanner-header">
            <h3>Signal Performance</h3>
            <p>Historical opening scanner signals, outcomes, and simulated equity curve.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    with filter_col1:
        signal_type = st.selectbox(
            "Signal type",
            ["All", "opening_scan", "premarket_scan"],
            index=0,
        )
    with filter_col2:
        horizon = st.selectbox("Equity horizon", ["1h", "1d", "3d"], index=1)
    with filter_col3:
        notional = st.number_input("Notional / trade ($)", min_value=100, max_value=5000, value=500, step=100)

    store = DataStore()
    type_filter = None if signal_type == "All" else signal_type
    rows = store.fetch_signals_with_outcomes(limit=500, signal_type=type_filter)
    signals_df, outcomes_df = parse_signal_history(rows)

    if signals_df.empty:
        st.info("No signals logged yet. Run the Opening Scanner or pre-market job to populate history.")
        _render_demo_charts()
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total signals", len(signals_df))
    c2.metric(
        "Avg score",
        f"{signals_df['score'].dropna().mean():.1f}" if signals_df["score"].notna().any() else "—",
    )
    c3.metric("Unique tickers", signals_df["ticker"].nunique())
    c4.metric("Labeled outcomes", len(outcomes_df))

    if not outcomes_df.empty:
        stats = compute_hit_rates(outcomes_df, signals_df, horizon=horizon)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric(f"{horizon} trades", stats["trades"])
        s2.metric("Win rate", f"{stats['win_rate']:.0%}")
        s3.metric("Avg return / trade", f"{stats['avg_return']:+.2%}")
        s4.metric("Sum return (dir-adj)", f"{stats['total_pnl_pct']:+.2%}")

        curve = build_equity_curve(
            outcomes_df,
            signals_df,
            horizon=horizon,
            notional_per_trade=float(notional),
        )
        if not curve.empty:
            st.subheader("Equity curve")
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=curve["created_at"],
                    y=curve["equity"],
                    mode="lines+markers",
                    name="Equity",
                    line=dict(width=2),
                )
            )
            fig.update_layout(
                title=f"Simulated equity ({horizon} horizon, ${notional:,.0f}/trade)",
                xaxis_title="Signal date",
                yaxis_title="Equity ($)",
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "Direction-aware PnL: long on gap-up signals, short on gap-down. "
                "Fixed notional per trade; not a full backtest."
            )

            with st.expander("Trade log"):
                display = curve.copy()
                display["trade_return"] = display["trade_return"].map(lambda x: f"{x:+.2%}")
                display["trade_pnl"] = display["trade_pnl"].map(lambda x: f"${x:+,.2f}")
                display["equity"] = display["equity"].map(lambda x: f"${x:,.2f}")
                display["cumulative_return"] = display["cumulative_return"].map(lambda x: f"{x:+.2%}")
                st.dataframe(display, use_container_width=True, hide_index=True)

        st.subheader("Outcome distribution")
        fig = px.histogram(
            outcomes_df,
            x="outcome_label",
            color="horizon",
            barmode="group",
            title="Labels by horizon",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Realized returns")
        fig2 = px.box(outcomes_df, x="horizon", y="realized_return", points="all")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.caption("Outcome labels appear once the labeling pipeline runs on historical data.")
        _render_score_distribution(signals_df)

    st.subheader("Signal history")
    history = signals_df.copy()
    if "score" in history.columns:
        history["score"] = history["score"].map(lambda x: f"{x:.0f}" if pd.notna(x) else "—")
    if "gap_pct" in history.columns:
        history["gap_pct"] = history["gap_pct"].map(
            lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
        )
    st.dataframe(history, use_container_width=True, hide_index=True)


def _render_score_distribution(signals_df: pd.DataFrame) -> None:
    if signals_df.empty or signals_df["score"].isna().all():
        return
    fig = px.histogram(signals_df, x="score", nbins=20, title="Signal score distribution")
    st.plotly_chart(fig, use_container_width=True)


def _render_demo_charts() -> None:
    """Placeholder calibration view when no live outcomes exist."""
    st.subheader("Score distribution (demo)")
    demo = pd.DataFrame({"score": [25, 35, 42, 55, 60, 72, 80, 45, 38, 50]})
    fig = px.histogram(demo, x="score", nbins=8, title="Expected score distribution")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Demo data shown until real signals are recorded.")
