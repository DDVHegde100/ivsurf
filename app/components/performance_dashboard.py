"""Signal performance dashboard tab."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from engine.data.storage import DataStore


def render_performance_dashboard() -> None:
    """Render signal history and performance metrics."""
    st.markdown(
        """
        <div class="scanner-header">
            <h3>Signal Performance</h3>
            <p>Historical opening scanner signals logged to local storage.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    store = DataStore()
    with store._connect() as conn:
        signal_rows = conn.execute(
            """
            SELECT s.id, s.ticker, s.signal_type, s.score, s.payload, s.created_at,
                   o.horizon, o.realized_return, o.label
            FROM signals s
            LEFT JOIN outcomes o ON o.signal_id = s.id
            ORDER BY s.created_at DESC
            LIMIT 200
            """
        ).fetchall()

    if not signal_rows:
        st.info("No signals logged yet. Run the Opening Scanner to populate history.")
        _render_demo_charts()
        return

    signals_df = pd.DataFrame(
        [
            {
                "id": r["id"],
                "ticker": r["ticker"],
                "signal_type": r["signal_type"],
                "score": r["score"],
                "created_at": r["created_at"],
                "gap_pct": _payload_field(r["payload"], "gap_pct"),
                "direction": _payload_field(r["payload"], "direction"),
            }
            for r in signal_rows
        ]
    ).drop_duplicates(subset=["id"])

    outcomes_df = pd.DataFrame(
        [
            {
                "signal_id": r["id"],
                "horizon": r["horizon"],
                "realized_return": r["realized_return"],
                "label": r["label"],
            }
            for r in signal_rows
            if r["horizon"] is not None
        ]
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Total signals", len(signals_df))
    c2.metric("Avg score", f"{signals_df['score'].dropna().mean():.1f}" if signals_df['score'].notna().any() else "—")
    c3.metric("Unique tickers", signals_df["ticker"].nunique())

    st.subheader("Recent signals")
    st.dataframe(signals_df, use_container_width=True, hide_index=True)

    if not outcomes_df.empty:
        st.subheader("Outcome distribution")
        fig = px.histogram(outcomes_df, x="label", color="horizon", barmode="group", title="Labels by horizon")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Realized returns")
        fig2 = px.box(outcomes_df, x="horizon", y="realized_return", points="all")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.caption("Outcome labels appear once the labeling pipeline runs on historical data.")
        _render_score_distribution(signals_df)


def _payload_field(payload: str | None, key: str):
    if not payload:
        return None
    try:
        data = json.loads(payload) if isinstance(payload, str) else payload
        return data.get(key)
    except Exception:
        return None


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
    st.caption("Demo data shown until real signal outcomes are recorded.")
