"""3D spectral amplitude surface plots."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from engine.spatial.spectral import fourier_amplitude_surface
from visuals.plot_3d.base import figure_3d, surface_from_grid


def plot_spectral_surface_3d(series: np.ndarray | None = None, *, title: str = "Fourier Amplitude Surface (3D)") -> go.Figure:
    if series is None:
        rng = np.random.default_rng(0)
        series = np.cumsum(rng.normal(0, 1, 200))
    tg, fg, amp = fourier_amplitude_surface(series)
    fig = figure_3d(title, x_title="Time", y_title="Frequency", z_title="Amplitude")
    fig.add_trace(surface_from_grid(tg, fg, amp, name="Spectrum", colorscale="Magma"))
    return fig
