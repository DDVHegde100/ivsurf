"""Export Plotly 3D figures to standalone HTML."""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go


def export_figure_html(fig: go.Figure, path: str | Path, *, include_plotlyjs: str = "cdn") -> Path:
    """Write an interactive 3D figure to a self-contained HTML file."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out), include_plotlyjs=include_plotlyjs, full_html=True)
    return out
