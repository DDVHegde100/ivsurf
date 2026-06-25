"""Parametric mathematical surfaces for 3D exploration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class ParametricSurface:
    name: str
    formula: str
    x_fn: Callable[[np.ndarray, np.ndarray], np.ndarray]
    y_fn: Callable[[np.ndarray, np.ndarray], np.ndarray]
    z_fn: Callable[[np.ndarray, np.ndarray], np.ndarray]
    u_range: tuple[float, float]
    v_range: tuple[float, float]


SURFACES: dict[str, ParametricSurface] = {
    "saddle": ParametricSurface(
        "Hyperbolic Paraboloid (Saddle)",
        "z = x² − y²",
        lambda u, v: u,
        lambda u, v: v,
        lambda u, v: u**2 - v**2,
        (-2.0, 2.0),
        (-2.0, 2.0),
    ),
    "sphere": ParametricSurface(
        "Sphere",
        "x = sin(u)cos(v), y = sin(u)sin(v), z = cos(u)",
        lambda u, v: np.sin(u) * np.cos(v),
        lambda u, v: np.sin(u) * np.sin(v),
        lambda u, v: np.cos(u),
        (0.0, np.pi),
        (0.0, 2 * np.pi),
    ),
    "torus": ParametricSurface(
        "Torus",
        "R=1.5, r=0.5",
        lambda u, v: (1.5 + 0.5 * np.cos(v)) * np.cos(u),
        lambda u, v: (1.5 + 0.5 * np.cos(v)) * np.sin(u),
        lambda u, v: 0.5 * np.sin(v),
        (0.0, 2 * np.pi),
        (0.0, 2 * np.pi),
    ),
    "ripple": ParametricSurface(
        "Ripple Wave",
        "z = sin(√(x² + y²))",
        lambda u, v: u,
        lambda u, v: v,
        lambda u, v: np.sin(np.sqrt(u**2 + v**2 + 1e-9)),
        (-6.0, 6.0),
        (-6.0, 6.0),
    ),
    "monkey_saddle": ParametricSurface(
        "Monkey Saddle",
        "z = x³ − 3xy²",
        lambda u, v: u,
        lambda u, v: v,
        lambda u, v: u**3 - 3 * u * v**2,
        (-1.5, 1.5),
        (-1.5, 1.5),
    ),
    "gaussian": ParametricSurface(
        "Gaussian Bell",
        "z = exp(−(x² + y²))",
        lambda u, v: u,
        lambda u, v: v,
        lambda u, v: np.exp(-(u**2 + v**2)),
        (-2.5, 2.5),
        (-2.5, 2.5),
    ),
}


def sample_surface(surface: ParametricSurface, n: int = 60) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample a parametric surface on a u/v grid."""
    u = np.linspace(surface.u_range[0], surface.u_range[1], n)
    v = np.linspace(surface.v_range[0], surface.v_range[1], n)
    ug, vg = np.meshgrid(u, v)
    return surface.x_fn(ug, vg), surface.y_fn(ug, vg), surface.z_fn(ug, vg)


def list_surfaces() -> list[str]:
    return list(SURFACES.keys())


def get_surface(key: str) -> ParametricSurface:
    return SURFACES[key]
