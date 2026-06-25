"""Covariance ellipsoid geometry for portfolio risk."""

from __future__ import annotations

import numpy as np


def covariance_ellipsoid_mesh(
    cov: np.ndarray,
    *,
    n: int = 40,
    scale: float = 2.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a 3D ellipsoid mesh from a covariance matrix (eigen-decomposition)."""
    cov = np.asarray(cov, dtype=float)
    if cov.shape != (3, 3):
        raise ValueError("cov must be 3x3")

    evals, evecs = np.linalg.eigh(cov)
    evals = np.clip(evals, 1e-12, None)
    radii = scale * np.sqrt(evals)

    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, n)
    ug, vg = np.meshgrid(u, v)
    xs = radii[0] * np.cos(ug) * np.sin(vg)
    ys = radii[1] * np.sin(ug) * np.sin(vg)
    zs = radii[2] * np.cos(vg)

    points = np.stack([xs, ys, zs], axis=-1)
    rotated = points @ evecs.T
    return rotated[..., 0], rotated[..., 1], rotated[..., 2]


def sample_portfolio_covariance() -> np.ndarray:
    """Example 3-asset covariance for demos."""
    vols = np.array([0.2, 0.25, 0.18])
    corr = np.array([[1.0, 0.6, 0.3], [0.6, 1.0, 0.4], [0.3, 0.4, 1.0]])
    return np.outer(vols, vols) * corr
