"""3D Spatial Lab — mathematical surfaces, ML graphs, and stock knowledge maps."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.spatial.animated import ANIMATIONS
from core.spatial.geometry import Vec3, angle_between, cross, distance, dot, normalize
from core.spatial.parametric import list_surfaces
from engine.data.universe import get_preset, parse_ticker_list
from engine.signals.opening_scanner import scan_universe
from engine.signals.regime_filter import RegimeFilter
from engine.spatial.knowledge_graph import build_sector_map
from visuals.plot_3d.animated import plot_animated_surface
from visuals.plot_3d.correlation import plot_correlation_sphere
from visuals.plot_3d.export import export_figure_html
from visuals.plot_3d.knowledge_graph import plot_knowledge_graph_3d
from visuals.plot_3d.mc_paths import plot_mc_path_cloud_3d
from visuals.plot_3d.ml_features import plot_ml_feature_space_3d
from visuals.plot_3d.ml_landscape import plot_ml_loss_landscape_3d
from visuals.plot_3d.nn_architecture import plot_nn_architecture_3d
from visuals.plot_3d.opening_terrain import plot_opening_score_terrain
from visuals.plot_3d.options_smile import plot_vol_smile_3d
from visuals.plot_3d.parametric import plot_parametric_surface
from visuals.plot_3d.price_paths import plot_price_path_3d, synthetic_price_path
from visuals.plot_3d.risk_ellipsoid import plot_risk_ellipsoid_3d
from visuals.plot_3d.spectral import plot_spectral_surface_3d


def render_spatial_lab_tab() -> None:
    """Render the 3D spatial analytics laboratory."""
    st.markdown(
        """
        <div class="scanner-header">
            <h3>3D Spatial Lab</h3>
            <p>Mathematical surfaces, ML graphs, knowledge maps, risk geometry, and exportable 3D views.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        ["MATH", "ML & NN", "MARKET", "RISK & OPTIONS", "PATHS & MC", "CALC", "EXPORT"]
    )
    tab_math, tab_ml, tab_market, tab_risk, tab_paths, tab_calc, tab_export = tabs

    with tab_math:
        _render_math_surfaces()

    with tab_ml:
        _render_ml_graphs()

    with tab_market:
        _render_market_3d()

    with tab_risk:
        _render_risk_options()

    with tab_paths:
        _render_paths_mc()

    with tab_calc:
        _render_spatial_calculator()

    with tab_export:
        _render_export_panel()


def _show_fig(fig, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, key=key)
    st.session_state["spatial_last_fig"] = fig


def _render_math_surfaces() -> None:
    st.subheader("Parametric & Animated Surfaces")
    mode = st.radio("Mode", ["Static", "Animated"], horizontal=True)
    resolution = st.slider("Grid resolution", 20, 100, 60, key="math_res")

    if mode == "Animated":
        anim = st.selectbox("Animation", list(ANIMATIONS.keys()))
        t = st.slider("Time phase", 0.0, 6.28, 0.0, 0.1)
        _show_fig(plot_animated_surface(anim, t, n=resolution), "anim")
        return

    surface_key = st.selectbox("Surface", list_surfaces(), index=0)
    _show_fig(plot_parametric_surface(surface_key, n=resolution), "static")


def _render_ml_graphs() -> None:
    st.subheader("ML & Neural Network 3D")
    ml_view = st.selectbox(
        "View",
        [
            "Loss landscape",
            "Feature space PCA",
            "Neural network architecture",
            "Fourier spectral surface",
        ],
    )

    if ml_view == "Loss landscape":
        st.caption("Log-loss surface over logistic regression weights.")
        _show_fig(plot_ml_loss_landscape_3d(), "loss")
        return

    if ml_view == "Neural network architecture":
        st.caption("3D topology of the default MLP volatility ranker architecture.")
        _show_fig(plot_nn_architecture_3d(), "nn")
        return

    if ml_view == "Fourier spectral surface":
        _show_fig(plot_spectral_surface_3d(), "spectral")
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
        _show_fig(plot_ml_feature_space_3d(st.session_state["spatial_scan_results"]), "pca")


def _render_market_3d() -> None:
    st.subheader("Stock & Scanner 3D Maps")
    market_view = st.selectbox(
        "View",
        ["Knowledge graph", "Correlation sphere", "Opening score terrain"],
    )
    tickers_raw = st.text_input("Tickers", value=", ".join(get_preset("core")[:16]), key="spatial_market_tickers")
    tickers = parse_ticker_list(tickers_raw)[:24]
    if not tickers:
        st.warning("Enter tickers.")
        return

    if market_view == "Knowledge graph":
        _show_fig(plot_knowledge_graph_3d(tickers), "kg")
        return

    if market_view == "Correlation sphere":
        sector_map = build_sector_map(tickers)
        _show_fig(plot_correlation_sphere(tickers, sector_map), "corr")
        return

    if st.button("Build score terrain", type="primary"):
        with st.spinner("Scanning..."):
            results = scan_universe(tickers, regime_filter=RegimeFilter(), min_score=0)
        st.session_state["spatial_terrain_results"] = results

    terrain_df = st.session_state.get("spatial_terrain_results")
    if terrain_df is not None and not terrain_df.empty:
        _show_fig(plot_opening_score_terrain(terrain_df), "terrain")


def _render_risk_options() -> None:
    st.subheader("Risk & Options 3D")
    view = st.radio("View", ["Risk ellipsoid", "IV smile surface"], horizontal=True)
    if view == "Risk ellipsoid":
        st.caption("3D covariance ellipsoid — 95% risk region for a 3-asset portfolio.")
        _show_fig(plot_risk_ellipsoid_3d(), "ellipsoid")
    else:
        spot = st.number_input("Spot price", value=100.0, min_value=1.0)
        _show_fig(plot_vol_smile_3d(spot=spot), "smile")


def _render_paths_mc() -> None:
    st.subheader("Price Paths & Monte Carlo")
    view = st.radio("View", ["Price ribbon", "MC path cloud"], horizontal=True)
    if view == "Price ribbon":
        df = synthetic_price_path(60)
        _show_fig(plot_price_path_3d(df), "ribbon")
    else:
        n_paths = st.slider("Paths", 10, 50, 25)
        _show_fig(plot_mc_path_cloud_3d(n_paths=n_paths), "mc")


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
        | **A · B** | `{dot(a, b):.4f}` |
        | **A × B** | `({c.x:.4f}, {c.y:.4f}, {c.z:.4f})` |
        | **\|A\|** | `{a.magnitude():.4f}` |
        | **dist(A, B)** | `{distance(a, b):.4f}` |
        | **angle(A, B)** | `{angle_between(a, b):.4f} rad` |
        """
    )

    import plotly.graph_objects as go
    from visuals.plot_3d.base import figure_3d

    fig = figure_3d("Vector Geometry", x_title="X", y_title="Y", z_title="Z")
    for vec, name, color in [(a, "A", "red"), (b, "B", "blue"), (c, "A×B", "green")]:
        fig.add_trace(
            go.Scatter3d(
                x=[0, vec.x], y=[0, vec.y], z=[0, vec.z],
                mode="lines+markers+text", text=["", name], name=name,
                line=dict(color=color, width=6), marker=dict(size=4, color=color),
            )
        )
    _show_fig(fig, "calc")


def _render_export_panel() -> None:
    st.subheader("Export 3D View")
    st.caption("Export the most recently rendered 3D chart as standalone HTML.")
    filename = st.text_input("Filename", value="openpulse_3d_export.html")
    if st.button("Export last chart to HTML", type="primary"):
        fig = st.session_state.get("spatial_last_fig")
        if fig is None:
            st.warning("Render a chart in another tab first.")
            return
        out = export_figure_html(fig, Path("data/exports") / filename)
        st.success(f"Exported to `{out}`")
