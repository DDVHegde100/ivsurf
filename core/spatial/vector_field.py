"""Numeric Jacobian demo for multivariate functions."""

from __future__ import annotations

import numpy as np


def numerical_jacobian(
    fn,
    point: np.ndarray,
    eps: float = 1e-5,
) -> np.ndarray:
    """Central-difference Jacobian at a 3D point for a R^3 -> R mapping."""
    point = np.asarray(point, dtype=float)
    base = fn(point)
    m = len(base) if hasattr(base, "__len__") else 1
    n = len(point)
    jac = np.zeros((m, n))
    for i in range(n):
        dp = np.zeros(n)
        dp[i] = eps
        fp = fn(point + dp)
        fm = fn(point - dp)
        jac[:, i] = (np.asarray(fp) - np.asarray(fm)) / (2 * eps)
    return jac


def demo_vector_field_grid(n: int = 15) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Sample f(x,y,z) = (sin x cos y, cos x sin z, sin y cos z) on a grid."""

    def f(p):
        x, y, z = p
        return np.array([np.sin(x) * np.cos(y), np.cos(x) * np.sin(z), np.sin(y) * np.cos(z)])

    lin = np.linspace(-1.5, 1.5, n)
    xg, yg, zg = np.meshgrid(lin, lin, lin, indexing="ij")
    u = np.sin(xg) * np.cos(yg)
    v = np.cos(xg) * np.sin(zg)
    w = np.sin(yg) * np.cos(zg)
    return xg, yg, zg, u, v, w
