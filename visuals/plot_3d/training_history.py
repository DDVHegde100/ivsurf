"""3D LSTM / MLP training history surface."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.spatial.training_history import synthetic_training_history, training_history_to_3d_grid
from visuals.plot_3d.base import figure_3d, surface_from_grid


def plot_training_history_3d(*, title: str = "Training History (3D)") -> go.Figure:
    hist = synthetic_training_history()
    eg, mg, zg = training_history_to_3d_grid(hist)
    fig = figure_3d(title, x_title="Epoch", y_title="Metric idx", z_title="Value")
    fig.add_trace(surface_from_grid(eg, mg, zg, name="Metrics", colorscale="Turbo"))
    return fig
