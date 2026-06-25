"""3D opening scanner score terrain."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.interpolate import griddata

import plotly.graph_objects as go

from visuals.plot_3d.base import figure_3d, scatter3d, surface_from_grid


def build_opening_terrain(
    results: pd.DataFrame,
    *,
    x_col: str = "gap_pct",
    y_col: str = "or_15m_range_pct",
    z_col: str = "opening_score",
    grid_n: int = 40,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    """Interpolate scan scores into a 3D terrain over gap × opening range."""
    numeric = results[[x_col, y_col, z_col]].astype(float).dropna()
    tickers = results.loc[numeric.index, "ticker"].astype(str)
    df = numeric.copy()
    df["ticker"] = tickers.values
    if df.empty:
        raise ValueError("No data for terrain")

    x = df[x_col].values
    y = df[y_col].values
    z = df[z_col].values

    xi = np.linspace(x.min(), x.max(), grid_n)
    yi = np.linspace(y.min(), y.max(), grid_n)
    xg, yg = np.meshgrid(xi, yi)
    zg = griddata((x, y), z, (xg, yg), method="cubic", fill_value=float(np.nanmean(z)))
    return xg, yg, zg, df


def plot_opening_score_terrain(results: pd.DataFrame, *, title: str = "Opening Score Terrain (3D)") -> go.Figure:
    xg, yg, zg, df = build_opening_terrain(results)
    fig = figure_3d(title, x_title="Gap %", y_title="OR 15m %", z_title="Opening Score")
    fig.add_trace(surface_from_grid(xg, yg, zg, name="Score terrain", colorscale="Plasma"))
    fig.add_trace(
        scatter3d(
            df["gap_pct"],
            df["or_15m_range_pct"],
            df["opening_score"],
            labels=df["ticker"].astype(str).tolist(),
            colors=df["opening_score"],
            name="Tickers",
            colorscale="Plasma",
        )
    )
    return fig
