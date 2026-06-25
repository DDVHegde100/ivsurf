"""3D implied volatility smile surface."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from visuals.plot_3d.base import figure_3d, surface_from_grid


def synthetic_vol_smile(
    spot: float = 100.0,
    *,
    n_strikes: int = 40,
    n_expiries: int = 30,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Synthetic strike × expiry × IV surface with smile skew."""
    strikes = np.linspace(spot * 0.8, spot * 1.2, n_strikes)
    expiries = np.linspace(0.05, 1.0, n_expiries)
    kg, eg = np.meshgrid(strikes, expiries, indexing="ij")
    moneyness = np.log(kg / spot)
    base_iv = 0.22 + 0.05 * np.exp(-eg * 2)
    skew = 0.15 * moneyness**2 + 0.08 * moneyness
    iv = base_iv + skew + 0.02 * np.sin(eg * 10)
    return kg, eg, np.clip(iv, 0.05, 0.8)


def plot_vol_smile_3d(spot: float = 100.0, *, title: str = "Implied Volatility Smile (3D)") -> go.Figure:
    kg, eg, iv = synthetic_vol_smile(spot)
    fig = figure_3d(title, x_title="Strike", y_title="Expiry (yrs)", z_title="IV")
    fig.add_trace(surface_from_grid(kg, eg, iv, name="IV surface", colorscale="Viridis"))
    return fig
