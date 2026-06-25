"""3D portfolio risk ellipsoid visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.spatial.risk_ellipsoid import covariance_ellipsoid_mesh, sample_portfolio_covariance
from visuals.plot_3d.base import figure_3d, surface_from_grid


def plot_risk_ellipsoid_3d(
    cov=None,
    *,
    title: str = "Portfolio Risk Ellipsoid (3D)",
    scale: float = 2.0,
) -> go.Figure:
    cov = sample_portfolio_covariance() if cov is None else cov
    xg, yg, zg = covariance_ellipsoid_mesh(cov, scale=scale)
    fig = figure_3d(title, x_title="Asset 1", y_title="Asset 2", z_title="Asset 3")
    fig.add_trace(surface_from_grid(xg, yg, zg, name="95% risk region", colorscale="Reds", opacity=0.75))
    fig.add_trace(
        go.Scatter3d(x=[0], y=[0], z=[0], mode="markers", marker=dict(size=6, color="yellow"), name="Portfolio")
    )
    return fig
