"""3D ML feature space scatter plots."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from engine.spatial.ml_feature_space import scan_results_to_feature_space
from visuals.plot_3d.base import figure_3d, scatter3d


def plot_ml_feature_space_3d(results: pd.DataFrame, *, title: str = "ML Feature Space (PCA 3D)") -> go.Figure:
    bundle = scan_results_to_feature_space(results)
    coords = bundle["coords"]
    fig = figure_3d(
        title,
        x_title=bundle["pc_labels"][0],
        y_title=bundle["pc_labels"][1],
        z_title=bundle["pc_labels"][2],
    )
    fig.add_trace(
        scatter3d(
            coords[:, 0],
            coords[:, 1],
            coords[:, 2],
            labels=bundle["tickers"],
            colors=bundle["scores"],
            name="Tickers",
            colorscale="Turbo",
        )
    )
    var = bundle["explained_variance"]
    fig.update_layout(
        title=f"{title}<br><sup>Explained variance: PC1={var[0]:.0%}, PC2={var[1]:.0%}, PC3={var[2]:.0%}</sup>"
    )
    return fig
