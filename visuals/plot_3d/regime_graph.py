"""3D Markov regime transition graph."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.spatial.regime_graph import default_transition_matrix, regime_transition_layout
from visuals.plot_3d.base import figure_3d, scatter3d


def plot_regime_graph_3d(*, title: str = "Regime Transition Graph (3D)") -> go.Figure:
    t = default_transition_matrix()
    xs, ys, zs, labels = regime_transition_layout(t)
    fig = figure_3d(title)
    fig.add_trace(scatter3d(xs, ys, zs, labels=labels, name="Regimes", colorscale="Set1"))

    n = len(xs)
    for i in range(n):
        for j in range(n):
            if i == j or t[i, j] < 0.03:
                continue
            fig.add_trace(
                go.Scatter3d(
                    x=[xs[i], xs[j]], y=[ys[i], ys[j]], z=[zs[i], zs[j]],
                    mode="lines",
                    line=dict(width=2 + 8 * t[i, j], color="rgba(255,200,0,0.5)"),
                    showlegend=False,
                    hoverinfo="text",
                    text=f"{labels[i]}→{labels[j]}: {t[i,j]:.0%}",
                )
            )
    return fig
