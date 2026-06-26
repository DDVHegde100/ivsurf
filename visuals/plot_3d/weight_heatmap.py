"""3D weight heatmap from sklearn MLP coefficients."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from sklearn.neural_network import MLPRegressor

from visuals.plot_3d.base import figure_3d, surface_from_grid


def _train_demo_mlp(seed: int = 42) -> MLPRegressor:
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(200, 8))
    y = x[:, 0] * 2 + x[:, 1] ** 2 - x[:, 2] * 0.5 + rng.normal(0, 0.1, 200)
    model = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=300, random_state=seed)
    model.fit(x, y)
    return model


def plot_weight_heatmap_3d(*, title: str = "Neural Network Weights (3D)") -> go.Figure:
    model = _train_demo_mlp()
    w = model.coefs_[0]  # input × hidden
    nr, nc = w.shape
    xg, yg = np.meshgrid(np.arange(nc), np.arange(nr))
    fig = figure_3d(title, x_title="Hidden unit", y_title="Input feature", z_title="Weight")
    fig.add_trace(surface_from_grid(xg, yg, w, name="Layer 1 weights", colorscale="RdBu"))
    return fig
