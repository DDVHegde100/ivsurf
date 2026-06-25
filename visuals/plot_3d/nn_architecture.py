"""3D neural network architecture visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.spatial.nn_graph import default_mlp_architecture, layout_architecture_3d
from visuals.plot_3d.base import figure_3d, scatter3d


def plot_nn_architecture_3d(*, title: str = "Neural Network Architecture (3D)") -> go.Figure:
    layers = default_mlp_architecture()
    nodes, edges = layout_architecture_3d(layers)

    xs = [n.x for n in nodes]
    ys = [n.y for n in nodes]
    zs = [n.z for n in nodes]
    labels = []
    idx = 0
    for layer in layers:
        count = min(layer.units, 12)
        labels.extend([f"{layer.name}" for _ in range(count)])
        idx += count

    fig = figure_3d(title, x_title="Layer", y_title="Y", z_title="Z")
    fig.add_trace(scatter3d(xs, ys, zs, labels=labels, name="Neurons", colorscale="Viridis"))

    ex, ey, ez = [], [], []
    for a, b in edges:
        ex.extend([nodes[a].x, nodes[b].x, None])
        ey.extend([nodes[a].y, nodes[b].y, None])
        ez.extend([nodes[a].z, nodes[b].z, None])
    fig.add_trace(
        go.Scatter3d(
            x=ex, y=ey, z=ez,
            mode="lines",
            line=dict(color="rgba(100,180,255,0.25)", width=1),
            name="Weights",
            hoverinfo="skip",
        )
    )
    return fig
