"""3D Greeks surface over strike and expiry."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from core.black_scholes import black_scholes_price
from core.greeks import delta, gamma, vega
from visuals.plot_3d.base import figure_3d, surface_from_grid


def greeks_surface(
    greek: str = "gamma",
    *,
    spot: float = 100.0,
    r: float = 0.05,
    sigma: float = 0.25,
    n: int = 35,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    strikes = np.linspace(spot * 0.7, spot * 1.3, n)
    expiries = np.linspace(0.05, 1.2, n)
    kg, eg = np.meshgrid(strikes, expiries, indexing="ij")
    zg = np.zeros_like(kg)
    for i in range(n):
        for j in range(n):
            k, t = float(kg[i, j]), float(eg[i, j])
            if greek == "delta":
                zg[i, j] = delta(spot, k, t, r, sigma, "call")
            elif greek == "gamma":
                zg[i, j] = gamma(spot, k, t, r, sigma, "call")
            elif greek == "vega":
                zg[i, j] = vega(spot, k, t, r, sigma, "call")
            else:
                zg[i, j] = black_scholes_price(spot, k, t, r, sigma, "call")
    return kg, eg, zg


def plot_greeks_surface_3d(greek: str = "gamma", *, title: str | None = None) -> go.Figure:
    title = title or f"{greek.title()} Surface (3D)"
    kg, eg, zg = greeks_surface(greek)
    fig = figure_3d(title, x_title="Strike", y_title="Expiry", z_title=greek.title())
    fig.add_trace(surface_from_grid(kg, eg, zg, name=greek, colorscale="Plasma"))
    return fig
