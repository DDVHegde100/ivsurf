"""3D knowledge graph layout for stock universes."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from core.spatial.geometry import Vec3, normalize, pairwise_distances


def _load_presets() -> dict[str, list[str]]:
    path = Path(__file__).resolve().parents[1] / "data" / "universes.json"
    data = json.loads(path.read_text())
    return {name: info["tickers"] for name, info in data["presets"].items()}


def build_sector_map(tickers: list[str]) -> dict[str, str]:
    """Map each ticker to the first preset sector that contains it."""
    presets = _load_presets()
    sector_map: dict[str, str] = {}
    for ticker in tickers:
        for preset, members in presets.items():
            if ticker in members:
                sector_map[ticker] = preset
                break
        sector_map.setdefault(ticker, "other")
    return sector_map


def build_knowledge_edges(tickers: list[str], sector_map: dict[str, str]) -> list[tuple[str, str, float]]:
    """Edges between tickers sharing a sector (knowledge graph)."""
    edges: list[tuple[str, str, float]] = []
    for i, a in enumerate(tickers):
        for b in tickers[i + 1 :]:
            if sector_map.get(a) == sector_map.get(b):
                edges.append((a, b, 1.0))
    return edges


def spring_layout_3d(
    tickers: list[str],
    edges: list[tuple[str, str, float]],
    *,
    iterations: int = 120,
    seed: int = 42,
) -> dict[str, Vec3]:
    """Simple 3D force-directed layout."""
    rng = np.random.default_rng(seed)
    positions = {t: Vec3(*rng.normal(0, 1, 3)) for t in tickers}
    index = {t: i for i, t in enumerate(tickers)}

    for _ in range(iterations):
        forces = {t: Vec3(0, 0, 0) for t in tickers}
        # Repulsion
        for i, a in enumerate(tickers):
            for b in tickers[i + 1 :]:
                delta = positions[a] - positions[b]
                dist = max(delta.magnitude(), 0.05)
                repulse = normalize(delta) * (0.08 / dist)
                forces[a] = forces[a] + repulse
                forces[b] = forces[b] - repulse
        # Attraction along edges
        for a, b, weight in edges:
            delta = positions[b] - positions[a]
            dist = max(delta.magnitude(), 0.05)
            attract = normalize(delta) * (0.02 * weight * dist)
            forces[a] = forces[a] + attract
            forces[b] = forces[b] - attract
        for t in tickers:
            positions[t] = positions[t] + forces[t] * 0.5

    # Center and scale
    arr = np.array([positions[t].as_array() for t in tickers])
    arr -= arr.mean(axis=0)
    scale = np.max(np.linalg.norm(arr, axis=1))
    if scale > 0:
        arr /= scale
    return {t: Vec3(float(arr[index[t], 0]), float(arr[index[t], 1]), float(arr[index[t], 2])) for t in tickers}
