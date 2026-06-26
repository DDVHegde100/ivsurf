"""3D vector field cone plot."""

from __future__ import annotations

import plotly.graph_objects as go

from core.spatial.vector_field import demo_vector_field_grid
from visuals.plot_3d.base import figure_3d


def plot_vector_field_3d(*, title: str = "Vector Field (3D)", step: int = 2) -> go.Figure:
    xg, yg, zg, u, v, w = demo_vector_field_grid(n=12)
    fig = figure_3d(title)
    fig.add_trace(
        go.Cone(
            x=xg[::step, ::step, ::step].flatten(),
            y=yg[::step, ::step, ::step].flatten(),
            z=zg[::step, ::step, ::step].flatten(),
            u=u[::step, ::step, ::step].flatten(),
            v=v[::step, ::step, ::step].flatten(),
            w=w[::step, ::step, ::step].flatten(),
            colorscale="Blues",
            sizemode="absolute",
            sizeref=0.4,
            name="Field",
        )
    )
    return fig
