"""Reusable Plotly 3D figure builders."""

from __future__ import annotations

from typing import Any, Callable, Sequence

import numpy as np
import plotly.graph_objects as go


def figure_3d(
    title: str,
    *,
    x_title: str = "X",
    y_title: str = "Y",
    z_title: str = "Z",
    width: int = 900,
    height: int = 700,
    eye: tuple[float, float, float] = (1.6, 1.6, 1.2),
) -> go.Figure:
    """Empty 3D figure with consistent scene styling."""
    fig = go.Figure()
    fig.update_layout(
        title={"text": title, "x": 0.5, "xanchor": "center"},
        width=width,
        height=height,
        margin=dict(l=0, r=0, t=50, b=0),
        scene=dict(
            xaxis_title=x_title,
            yaxis_title=y_title,
            zaxis_title=z_title,
            aspectmode="data",
            camera=dict(eye=dict(x=eye[0], y=eye[1], z=eye[2])),
        ),
    )
    return fig


def surface_from_grid(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    *,
    name: str = "Surface",
    colorscale: str = "Viridis",
    opacity: float = 0.9,
) -> go.Surface:
    """Build a Plotly Surface trace from mesh grids."""
    return go.Surface(
        x=x,
        y=y,
        z=z,
        name=name,
        colorscale=colorscale,
        opacity=opacity,
        showscale=True,
    )


def scatter3d(
    x: Sequence[float],
    y: Sequence[float],
    z: Sequence[float],
    *,
    labels: Sequence[str] | None = None,
    colors: Sequence[float] | None = None,
    sizes: Sequence[float] | None = None,
    name: str = "Points",
    colorscale: str = "Turbo",
    text: Sequence[str] | None = None,
) -> go.Scatter3d:
    """Build a labeled 3D scatter trace."""
    marker: dict[str, Any] = {"size": 6, "opacity": 0.9}
    if colors is not None:
        marker["color"] = list(colors)
        marker["colorscale"] = colorscale
        marker["showscale"] = True
        marker["colorbar"] = dict(title="Value")
    if sizes is not None:
        marker["size"] = list(sizes)

    hover = text
    if hover is None and labels is not None:
        hover = [str(label) for label in labels]

    return go.Scatter3d(
        x=list(x),
        y=list(y),
        z=list(z),
        mode="markers+text" if labels is not None else "markers",
        text=list(labels) if labels is not None else None,
        textposition="top center",
        hovertext=hover,
        hoverinfo="text",
        name=name,
        marker=marker,
    )


def mesh_from_grid(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    *,
    name: str = "Mesh",
    color: str = "cyan",
    opacity: float = 0.35,
) -> go.Mesh3d:
    """Triangulated mesh from a regular grid (for parametric surfaces)."""
    ny, nx = z.shape
    vertices_x: list[float] = []
    vertices_y: list[float] = []
    vertices_z: list[float] = []
    i_idx: list[int] = []
    j_idx: list[int] = []
    k_idx: list[int] = []

    for row in range(ny):
        for col in range(nx):
            vertices_x.append(float(x[row, col]))
            vertices_y.append(float(y[row, col]))
            vertices_z.append(float(z[row, col]))

    def vid(r: int, c: int) -> int:
        return r * nx + c

    for row in range(ny - 1):
        for col in range(nx - 1):
            a, b, c, d = vid(row, col), vid(row, col + 1), vid(row + 1, col + 1), vid(row + 1, col)
            i_idx.extend([a, a])
            j_idx.extend([b, c])
            k_idx.extend([c, d])

    return go.Mesh3d(
        x=vertices_x,
        y=vertices_y,
        z=vertices_z,
        i=i_idx,
        j=j_idx,
        k=k_idx,
        name=name,
        opacity=opacity,
        color=color,
        flatshading=True,
    )


def add_wireframe_box(
    fig: go.Figure,
    *,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    zmin: float,
    zmax: float,
    color: str = "white",
) -> go.Figure:
    """Add a bounding box wireframe to an existing 3D figure."""
    corners = [
        (xmin, ymin, zmin),
        (xmax, ymin, zmin),
        (xmax, ymax, zmin),
        (xmin, ymax, zmin),
        (xmin, ymin, zmax),
        (xmax, ymin, zmax),
        (xmax, ymax, zmax),
        (xmin, ymax, zmax),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    xs, ys, zs = [], [], []
    for a, b in edges:
        xs.extend([corners[a][0], corners[b][0], None])
        ys.extend([corners[a][1], corners[b][1], None])
        zs.extend([corners[a][2], corners[b][2], None])
    fig.add_trace(
        go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color=color, width=2), name="Bounds")
    )
    return fig


def grid_from_function(
    fn: Callable[[np.ndarray, np.ndarray], np.ndarray],
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    n: int = 60,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample a scalar field z = fn(x, y) on a regular grid."""
    xs = np.linspace(x_range[0], x_range[1], n)
    ys = np.linspace(y_range[0], y_range[1], n)
    xg, yg = np.meshgrid(xs, ys)
    zg = fn(xg, yg)
    return xg, yg, zg
