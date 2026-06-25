"""3D correlation sphere visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.spatial.correlation_layout import layout_tickers_3d
from visuals.plot_3d.base import figure_3d, scatter3d


def plot_correlation_sphere(
    tickers: list[str],
    sector_map: dict[str, str],
    *,
    title: str = "3D Correlation Sphere",
) -> go.Figure:
    positions = layout_tickers_3d(tickers, sector_map)
    xs = [positions[t][0] for t in tickers]
    ys = [positions[t][1] for t in tickers]
    zs = [positions[t][2] for t in tickers]
    sectors = [sector_map.get(t, "unknown") for t in tickers]
    sector_ids = {s: i for i, s in enumerate(sorted(set(sectors)))}
    colors = [sector_ids[s] for s in sectors]

    fig = figure_3d(title, x_title="Dim 1", y_title="Dim 2", z_title="Dim 3")
    fig.add_trace(
        scatter3d(xs, ys, zs, labels=tickers, colors=colors, name="Tickers", colorscale="Set2")
    )

    # Reference sphere wireframe
    import numpy as np

    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 20)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))
    fig.add_trace(
        go.Surface(x=x, y=y, z=z, opacity=0.08, colorscale="Greys", showscale=False, name="Unit sphere")
    )
    return fig
