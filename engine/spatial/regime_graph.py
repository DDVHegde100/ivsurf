"""3D Markov regime transition visualization."""

from __future__ import annotations

import numpy as np


def regime_transition_layout(
    transition_matrix: np.ndarray | None = None,
    *,
    n_regimes: int = 3,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """
    Place regimes on a 3D simplex and return node positions + transition strengths.
    """
    if transition_matrix is None:
        t = np.full((n_regimes, n_regimes), 1 / n_regimes)
        np.fill_diagonal(t, 0.6)
        t = t / t.sum(axis=1, keepdims=True)
        transition_matrix = t

    # Simplex coordinates in 3D
    angles = np.linspace(0, 2 * np.pi, n_regimes, endpoint=False)
    xs = np.cos(angles)
    ys = np.sin(angles)
    zs = np.linspace(-0.5, 0.5, n_regimes)
    labels = [f"Regime {i}" for i in range(n_regimes)]
    return xs, ys, zs, labels


def default_transition_matrix() -> np.ndarray:
    return np.array([
        [0.95, 0.04, 0.01],
        [0.05, 0.90, 0.05],
        [0.02, 0.08, 0.90],
    ])
