"""Geometric Brownian motion path clouds in 3D."""

from __future__ import annotations

import numpy as np


def simulate_gbm_paths(
    *,
    n_paths: int = 30,
    n_steps: int = 100,
    s0: float = 100.0,
    mu: float = 0.05,
    sigma: float = 0.2,
    dt: float = 1 / 252,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns (time_grid, paths, terminal_values) where paths shape is (n_paths, n_steps).
    """
    rng = np.random.default_rng(seed)
    times = np.arange(n_steps) * dt
    paths = np.zeros((n_paths, n_steps))
    paths[:, 0] = s0
    for t in range(1, n_steps):
        z = rng.standard_normal(n_paths)
        paths[:, t] = paths[:, t - 1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)
    return times, paths, paths[:, -1]
