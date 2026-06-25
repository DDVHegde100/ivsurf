"""Time-varying parametric surfaces for animation."""

from __future__ import annotations

import numpy as np


def ripple_surface(t: float, n: int = 60) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Ripple wave z = sin(sqrt(x²+y²) - ωt) at time t."""
    u = np.linspace(-6, 6, n)
    v = np.linspace(-6, 6, n)
    xg, yg = np.meshgrid(u, v)
    r = np.sqrt(xg**2 + yg**2 + 1e-9)
    zg = np.sin(r - 2.5 * t)
    return xg, yg, zg


def lissajous_knot(t: float, n: int = 80) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """3D Lissajous knot parameterized by phase t."""
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, 2 * np.pi, n)
    ug, vg = np.meshgrid(u, v)
    xg = np.sin(3 * ug + t) * np.cos(vg)
    yg = np.sin(2 * ug + t * 0.7) * np.sin(vg)
    zg = np.cos(ug + t) * np.cos(2 * vg)
    return xg, yg, zg


def breathing_sphere(t: float, n: int = 50) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sphere with pulsating radius."""
    u = np.linspace(0, np.pi, n)
    v = np.linspace(0, 2 * np.pi, n)
    ug, vg = np.meshgrid(u, v)
    r = 1.0 + 0.25 * np.sin(t)
    xg = r * np.sin(ug) * np.cos(vg)
    yg = r * np.sin(ug) * np.sin(vg)
    zg = r * np.cos(ug)
    return xg, yg, zg


ANIMATIONS = {
    "ripple": ripple_surface,
    "lissajous": lissajous_knot,
    "breathing_sphere": breathing_sphere,
}


def sample_animation(name: str, t: float, n: int = 60) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fn = ANIMATIONS[name]
    return fn(t, n=n)
