"""Animated 3D surface plots."""

from __future__ import annotations

import plotly.graph_objects as go

from core.spatial.animated import ANIMATIONS, sample_animation
from visuals.plot_3d.base import figure_3d, surface_from_grid


def plot_animated_surface(name: str, t: float, *, n: int = 60) -> go.Figure:
    if name not in ANIMATIONS:
        raise ValueError(f"Unknown animation '{name}'. Options: {list(ANIMATIONS)}")
    xg, yg, zg = sample_animation(name, t, n=n)
    fig = figure_3d(f"Animated: {name} (t={t:.2f})")
    fig.add_trace(surface_from_grid(xg, yg, zg, colorscale="Turbo"))
    return fig
