"""Plot parametric mathematical surfaces in 3D."""

from __future__ import annotations

import plotly.graph_objects as go

from core.spatial.parametric import ParametricSurface, get_surface, sample_surface
from visuals.plot_3d.base import figure_3d, mesh_from_grid, surface_from_grid


def plot_parametric_surface(key: str, *, n: int = 60) -> go.Figure:
    surface = get_surface(key)
    xg, yg, zg = sample_surface(surface, n=n)
    fig = figure_3d(surface.name, x_title="X", y_title="Y", z_title="Z")
    fig.add_trace(surface_from_grid(xg, yg, zg, name=surface.name))
    fig.add_trace(mesh_from_grid(xg, yg, zg, name="Wire mesh", opacity=0.15))
    fig.update_layout(title=f"{surface.name}<br><sup>{surface.formula}</sup>")
    return fig


def plot_custom_height_field(
    z_fn,
    x_range: tuple[float, float] = (-3, 3),
    y_range: tuple[float, float] = (-3, 3),
    *,
    title: str = "Custom height field",
    n: int = 60,
) -> go.Figure:
    from visuals.plot_3d.base import grid_from_function

    xg, yg, zg = grid_from_function(z_fn, x_range, y_range, n=n)
    fig = figure_3d(title)
    fig.add_trace(surface_from_grid(xg, yg, zg))
    return fig
