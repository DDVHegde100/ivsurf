"""3D Heston implied volatility surface plot."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.spatial.heston_surface import heston_iv_surface
from visuals.plot_3d.base import figure_3d, surface_from_grid


def plot_heston_surface_3d(*, title: str = "Heston IV Surface (3D)") -> go.Figure:
    kg, eg, iv = heston_iv_surface()
    fig = figure_3d(title, x_title="Strike", y_title="Expiry", z_title="IV")
    fig.add_trace(surface_from_grid(kg, eg, iv, name="Heston IV", colorscale="Cividis"))
    return fig
