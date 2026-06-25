"""3D Monte Carlo price path cloud."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.spatial.monte_carlo_paths import simulate_gbm_paths
from visuals.plot_3d.base import figure_3d


def plot_mc_path_cloud_3d(*, title: str = "Monte Carlo Path Cloud (3D)", n_paths: int = 25) -> go.Figure:
    times, paths, terminal = simulate_gbm_paths(n_paths=n_paths)
    fig = figure_3d(title, x_title="Time (yrs)", y_title="Path #", z_title="Price")

    for i in range(paths.shape[0]):
        fig.add_trace(
            go.Scatter3d(
                x=times,
                y=[i] * len(times),
                z=paths[i],
                mode="lines",
                line=dict(width=2, color=terminal[i], colorscale="Portland"),
                showlegend=False,
                hoverinfo="skip",
            )
        )
    return fig
