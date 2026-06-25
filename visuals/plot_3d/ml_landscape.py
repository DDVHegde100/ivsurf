"""3D ML loss landscape visualization."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import make_classification

from visuals.plot_3d.base import figure_3d, scatter3d, surface_from_grid


def synthetic_loss_landscape(
    *,
    n_grid: int = 50,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a 3D loss surface over two weight dimensions for a logistic model.

    Returns grid (xg, yg, loss), and training points projected to feature dims.
    """
    x, y = make_classification(n_samples=80, n_features=2, n_redundant=0, random_state=seed)
    w0 = np.linspace(-4, 4, n_grid)
    w1 = np.linspace(-4, 4, n_grid)
    xg, yg = np.meshgrid(w0, w1)
    loss_grid = np.zeros_like(xg)

    for i in range(n_grid):
        for j in range(n_grid):
            wx, wy = xg[i, j], yg[i, j]
            logits = wx * x[:, 0] + wy * x[:, 1]
            probs = 1 / (1 + np.exp(-logits))
            eps = 1e-9
            loss_grid[i, j] = -np.mean(y * np.log(probs + eps) + (1 - y) * np.log(1 - probs + eps))
            loss_grid[i, j] += 0.01 * (wx**2 + wy**2)

    return xg, yg, loss_grid, x[:, 0], x[:, 1], y, y.astype(float)


def plot_ml_loss_landscape_3d(*, title: str = "ML Loss Landscape (3D)") -> go.Figure:
    xg, yg, zg, px, py, _, labels = synthetic_loss_landscape()
    fig = figure_3d(title, x_title="Weight w₁", y_title="Weight w₂", z_title="Log loss")
    fig.add_trace(surface_from_grid(xg, yg, zg, name="Loss surface", colorscale="Inferno"))
    fig.add_trace(
        scatter3d(
            px,
            py,
            np.zeros_like(px),
            colors=labels,
            name="Training samples",
            colorscale="Set1",
        )
    )
    return fig
