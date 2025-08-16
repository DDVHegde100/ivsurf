"""
Heatmap plotting utilities (placeholder).

Planned: Greeks heatmaps, IV heatmaps, correlation matrices.
"""

import plotly.express as px
import pandas as pd


def greeks_heatmap(df: pd.DataFrame, value_col: str = "vega"):
    """Assumes df has columns: strike, expiry, <value_col>."""
    if not {"strike", "expiry", value_col}.issubset(df.columns):
        raise ValueError("DataFrame must contain strike, expiry, and value_col")
    pivot = df.pivot_table(index="expiry", columns="strike", values=value_col)
    fig = px.imshow(pivot, aspect="auto", origin="lower", color_continuous_scale="Viridis",
                    labels=dict(color=value_col))
    fig.update_layout(title=f"{value_col.capitalize()} Heatmap")
    return fig
