"""Embed correlation matrices into 3D space."""

from __future__ import annotations

import numpy as np
from sklearn.manifold import MDS


def correlation_from_sectors(tickers: list[str], sector_map: dict[str, str]) -> np.ndarray:
    """Build a synthetic correlation matrix from sector membership."""
    n = len(tickers)
    corr = np.eye(n, dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            same = sector_map.get(tickers[i], "unknown") == sector_map.get(tickers[j], "unknown")
            rho = 0.75 if same else 0.25
            corr[i, j] = corr[j, i] = rho
    return corr


def embed_correlation_3d(corr: np.ndarray) -> np.ndarray:
    """MDS embedding of a correlation matrix into 3D."""
    dist = np.sqrt(np.clip(2 * (1 - corr), 0, None))
    np.fill_diagonal(dist, 0.0)
    mds = MDS(n_components=3, dissimilarity="precomputed", random_state=42, normalized_stress="auto")
    coords = mds.fit_transform(dist)
    # Normalize to unit sphere for stable visualization
    norms = np.linalg.norm(coords, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return coords / norms


def layout_tickers_3d(
    tickers: list[str],
    sector_map: dict[str, str],
) -> dict[str, tuple[float, float, float]]:
    """Return ticker -> (x, y, z) positions from sector-based correlation."""
    corr = correlation_from_sectors(tickers, sector_map)
    coords = embed_correlation_3d(corr)
    return {ticker: (float(coords[i, 0]), float(coords[i, 1]), float(coords[i, 2])) for i, ticker in enumerate(tickers)}
