"""Shared 3D Plotly visualization helpers."""

from visuals.plot_3d.base import (
    add_wireframe_box,
    figure_3d,
    mesh_from_grid,
    scatter3d,
    surface_from_grid,
)

__all__ = [
    "figure_3d",
    "surface_from_grid",
    "scatter3d",
    "mesh_from_grid",
    "add_wireframe_box",
]
