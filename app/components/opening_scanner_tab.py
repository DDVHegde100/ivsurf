"""Opening hours volatility scanner tab."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from engine.data.storage import DataStore
from engine.signals.opening_scanner import scan_universe
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

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        tickers_raw = st.text_input(
            "Tickers (comma-separated)",
            value=", ".join(DEFAULT_TICKERS[:12]),
        )
    with col2:
        min_score = st.slider("Min score", 0, 80, 20)
    with col3:
        use_regime = st.checkbox("Regime filter", value=True)

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


def _format_scanner_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "price" in out.columns:
        out["price"] = out["price"].map(lambda x: f"${x:.2f}")
    if "gap_pct" in out.columns:
        out["gap_pct"] = out["gap_pct"].map(lambda x: f"{x:+.2f}%")
    if "opening_score" in out.columns:
        out["opening_score"] = out["opening_score"].map(lambda x: f"{x:.0f}")
    if "volatility" in out.columns:
        out["volatility"] = out["volatility"].map(lambda x: f"{x:.1%}")
    if "premarket_volume_ratio" in out.columns:
        out["premarket_volume_ratio"] = out["premarket_volume_ratio"].map(lambda x: f"{x:.2f}x")
    if "relative_volume_open" in out.columns:
        out["relative_volume_open"] = out["relative_volume_open"].map(lambda x: f"{x:.2f}x")
    if "or_15m_range_pct" in out.columns:
        out["or_15m_range_pct"] = out["or_15m_range_pct"].map(lambda x: f"{x:.2f}%")
    return out
