"""3D stock knowledge graph visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from engine.spatial.knowledge_graph import build_knowledge_edges, build_sector_map, spring_layout_3d
from visuals.plot_3d.base import figure_3d, scatter3d


def plot_knowledge_graph_3d(tickers: list[str], *, title: str = "Stock Knowledge Graph (3D)") -> go.Figure:
    sector_map = build_sector_map(tickers)
    edges = build_knowledge_edges(tickers, sector_map)
    layout = spring_layout_3d(tickers, edges)

    xs = [layout[t].x for t in tickers]
    ys = [layout[t].y for t in tickers]
    zs = [layout[t].z for t in tickers]
    sectors = [sector_map[t] for t in tickers]
    sector_ids = {s: i for i, s in enumerate(sorted(set(sectors)))}
    colors = [sector_ids[s] for s in sectors]

    fig = figure_3d(title)
    fig.add_trace(scatter3d(xs, ys, zs, labels=tickers, colors=colors, name="Tickers", colorscale="Portland"))

    edge_x, edge_y, edge_z = [], [], []
    for a, b, _ in edges:
        edge_x.extend([layout[a].x, layout[b].x, None])
        edge_y.extend([layout[a].y, layout[b].y, None])
        edge_z.extend([layout[a].z, layout[b].z, None])
    fig.add_trace(
        go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode="lines",
            line=dict(color="rgba(120,120,120,0.35)", width=2),
            name="Sector links",
            hoverinfo="skip",
        )
    )
    return fig
