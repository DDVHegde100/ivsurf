"""Spectral / Fourier 3D surfaces from time series."""

from __future__ import annotations

import numpy as np


def fourier_amplitude_surface(series: np.ndarray, *, n_time: int = 50, n_freq: int = 40) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build time × frequency × amplitude surface via sliding-window FFT.
    """
    series = np.asarray(series, dtype=float).ravel()
    if len(series) < n_time + n_freq:
        raise ValueError("series too short for spectral surface")

    freqs = np.fft.rfftfreq(n_freq, d=1.0)[: n_freq // 2]
    time_idx = np.arange(n_time)
    amp = np.zeros((len(time_idx), len(freqs)))

    for i, start in enumerate(time_idx):
        window = series[start : start + n_freq]
        spectrum = np.abs(np.fft.rfft(window))[: len(freqs)]
        amp[i, :] = spectrum

    tg, fg = np.meshgrid(time_idx, freqs, indexing="ij")
    return tg, fg, amp
