"""Rolling correlation tube paths in 3D."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


def rolling_correlation_paths(
    *,
    n_assets: int = 3,
    n_windows: int = 50,
    window: int = 20,
    seed: int = 42,
) -> tuple[np.ndarray, list[np.ndarray]]:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0, 0.02, (n_windows + window, n_assets))
    paths = []
    for i in range(n_windows):
        chunk = returns[i : i + window]
        corr = np.corrcoef(chunk.T)
        paths.append(corr[np.triu_indices(n_assets, k=1)])
    time = np.arange(n_windows)
    return time, paths


def plot_correlation_tubes_3d(*, title: str = "Rolling Correlation Tubes (3D)") -> go.Figure:
    time, paths = rolling_correlation_paths()
    arr = np.array(paths)
    fig = go.Figure()
    for j in range(arr.shape[1]):
        fig.add_trace(
            go.Scatter3d(
                x=time,
                y=[j] * len(time),
                z=arr[:, j],
                mode="lines",
                name=f"Pair {j}",
                line=dict(width=4),
            )
        )
    fig.update_layout(
        title=title,
        scene=dict(xaxis_title="Window", yaxis_title="Pair", zaxis_title="Correlation"),
        height=700,
    )
    return fig
