"""3D opening range scatter from live snapshots."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.feed.opening_range import OpeningRangeFeed
from visuals.plot_3d.base import figure_3d, scatter3d


def plot_opening_range_3d(tickers: list[str], *, title: str = "Opening Range (3D)") -> go.Figure:
    feed = OpeningRangeFeed()
    snapshots = feed.snapshots(tickers)
    if not snapshots:
        raise ValueError("No opening range data")

    xs = [s["gap_pct"] for s in snapshots]
    ys = [s["windows"].get("15m", {}).get("range_pct", 0) for s in snapshots]
    zs = [s["relative_volume_open"] for s in snapshots]
    labels = [s["ticker"] for s in snapshots]
    colors = [1 if s.get("breakout") == "above" else (-1 if s.get("breakout") == "below" else 0) for s in snapshots]

    fig = figure_3d(title, x_title="Gap %", y_title="OR 15m %", z_title="Rel vol")
    fig.add_trace(scatter3d(xs, ys, zs, labels=labels, colors=colors, name="Tickers", colorscale="RdYlGn"))
    return fig
