"""3D Spatial Lab — mathematical surfaces, ML graphs, and stock knowledge maps."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from core.spatial.parametric import list_surfaces
from core.spatial.geometry import Vec3, dot, cross, distance, normalize, angle_between
from engine.data.universe import get_preset, parse_ticker_list
from engine.signals.opening_scanner import scan_universe
from engine.signals.regime_filter import RegimeFilter
from engine.spatial.knowledge_graph import build_sector_map
from visuals.plot_3d.correlation import plot_correlation_sphere
from visuals.plot_3d.knowledge_graph import plot_knowledge_graph_3d
from visuals.plot_3d.ml_features import plot_ml_feature_space_3d
from visuals.plot_3d.ml_landscape import plot_ml_loss_landscape_3d
from visuals.plot_3d.opening_terrain import plot_opening_score_terrain
from visuals.plot_3d.parametric import plot_parametric_surface


def render_spatial_lab_tab() -> None:
    """Render the 3D spatial analytics laboratory."""
    st.markdown(
        """
        <div class="scanner-header">
            <h3>3D Spatial Lab</h3>
            <p>Mathematical surfaces, ML loss landscapes, knowledge graphs, and 3D market geometry.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_math, tab_ml, tab_market, tab_calc = st.tabs(
        ["MATH SURFACES", "ML GRAPHS", "MARKET 3D", "SPATIAL CALC"]
    )

    with tab_math:
        _render_math_surfaces()

    with tab_ml:
        _render_ml_graphs()

    with tab_market:
        _render_market_3d()

    with tab_calc:
        _render_spatial_calculator()


def _render_math_surfaces() -> None:
    st.subheader("Parametric Mathematical Surfaces")
    surface_key = st.selectbox("Surface", list_surfaces(), index=0)
    resolution = st.slider("Grid resolution", 20, 100, 60)
    fig = plot_parametric_surface(surface_key, n=resolution)
    st.plotly_chart(fig, use_container_width=True)


def _render_ml_graphs() -> None:
    st.subheader("ML Visualizations")
    ml_view = st.radio("View", ["Loss landscape (3D)", "Feature space PCA (3D)"], horizontal=True)

    if ml_view == "Loss landscape (3D)":
        st.caption("Log-loss surface over logistic regression weights with training samples.")
        st.plotly_chart(plot_ml_loss_landscape_3d(), use_container_width=True)
        return

    tickers_raw = st.text_input("Tickers for feature PCA", value=", ".join(get_preset("opening")))
    tickers = parse_ticker_list(tickers_raw)
    if st.button("Build feature space", type="primary"):
        with st.spinner("Scanning for feature vectors..."):
            results = scan_universe(tickers, regime_filter=RegimeFilter(), min_score=0)
        if results.empty:
            st.warning("No scan data — try different tickers.")
            return
        st.session_state["spatial_scan_results"] = results

    if "spatial_scan_results" in st.session_state:
        df = st.session_state["spatial_scan_results"]
        st.plotly_chart(plot_ml_feature_space_3d(df), use_container_width=True)


def _render_market_3d() -> None:
    st.subheader("Stock & Scanner 3D Maps")
    market_view = st.radio(
        "View",
        ["Knowledge graph", "Correlation sphere", "Opening score terrain"],
        horizontal=True,
    )
    tickers_raw = st.text_input("Tickers", value=", ".join(get_preset("core")[:16]), key="spatial_market_tickers")
    tickers = parse_ticker_list(tickers_raw)[:24]
    if not tickers:
        st.warning("Enter tickers.")
        return

    if market_view == "Knowledge graph":
        st.plotly_chart(plot_knowledge_graph_3d(tickers), use_container_width=True)
        return

    if market_view == "Correlation sphere":
        sector_map = build_sector_map(tickers)
        st.plotly_chart(plot_correlation_sphere(tickers, sector_map), use_container_width=True)
        return

    if st.button("Build score terrain", type="primary"):
        with st.spinner("Scanning..."):
            results = scan_universe(tickers, regime_filter=RegimeFilter(), min_score=0)
        st.session_state["spatial_terrain_results"] = results

    terrain_df = st.session_state.get("spatial_terrain_results")
    if terrain_df is not None and not terrain_df.empty:
        st.plotly_chart(plot_opening_score_terrain(terrain_df), use_container_width=True)


def _render_spatial_calculator() -> None:
    st.subheader("3D Vector & Geometry Calculator")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Vector A**")
        ax = st.number_input("A.x", value=1.0, key="ax")
        ay = st.number_input("A.y", value=0.0, key="ay")
        az = st.number_input("A.z", value=0.0, key="az")
    with c2:
        st.markdown("**Vector B**")
        bx = st.number_input("B.x", value=0.0, key="bx")
        by = st.number_input("B.y", value=1.0, key="by")
        bz = st.number_input("B.z", value=0.0, key="bz")

    a, b = Vec3(ax, ay, az), Vec3(bx, by, bz)
    c = cross(a, b)
    st.markdown(
        f"""
        | Operation | Result |
        |-----------|--------|
        | **A · B** (dot) | `{dot(a, b):.4f}` |
        | **A × B** (cross) | `({c.x:.4f}, {c.y:.4f}, {c.z:.4f})` |
        | **\|A\|** | `{a.magnitude():.4f}` |
        | **dist(A, B)** | `{distance(a, b):.4f}` |
        | **angle(A, B)** | `{angle_between(a, b):.4f} rad` |
        | **Â** (unit) | `({normalize(a).x:.4f}, {normalize(a).y:.4f}, {normalize(a).z:.4f})` |
        """
    )

    import plotly.graph_objects as go
    from visuals.plot_3d.base import figure_3d

    fig = figure_3d("Vector Geometry", x_title="X", y_title="Y", z_title="Z")
    for vec, name, color in [(a, "A", "red"), (b, "B", "blue"), (c, "A×B", "green")]:
        fig.add_trace(
            go.Scatter3d(
                x=[0, vec.x],
                y=[0, vec.y],
                z=[0, vec.z],
                mode="lines+markers+text",
                text=["", name],
                name=name,
                line=dict(color=color, width=6),
                marker=dict(size=4, color=color),
            )
        )
    st.plotly_chart(fig, use_container_width=True)
