"""3D price path ribbon plots."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from visuals.plot_3d.base import figure_3d


def synthetic_price_path(days: int = 60, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0005, 0.015, days)
    price = 100 * np.cumprod(1 + returns)
    volume = rng.integers(1_000_000, 5_000_000, days)
    t = np.arange(days)
    return pd.DataFrame({"day": t, "price": price, "volume": volume / 1e6})


def plot_price_path_3d(df: pd.DataFrame, *, title: str = "Price Path Ribbon (3D)") -> go.Figure:
    fig = figure_3d(title, x_title="Day", y_title="Price", z_title="Volume (M)")
    fig.add_trace(
        go.Scatter3d(
            x=df["day"],
            y=df["price"],
            z=df["volume"],
            mode="lines+markers",
            line=dict(color=df["price"], colorscale="Viridis", width=4),
            marker=dict(size=3),
            name="Path",
        )
    )
    return fig
